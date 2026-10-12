"""Private Oxen media storage with expiring, independently verified download URLs."""
import hashlib
import json
import mimetypes
import re
import uuid
import time
from pathlib import Path
from urllib.parse import quote, urlparse, parse_qs

import requests
import xxhash
from config import credential, setting

API = 'https://hub.oxen.ai/api'


class MediaLinkError(ValueError):
    """Media validation failed before generation submission."""


def headers():
    return {'Authorization': 'Bearer ' + credential('OXEN_API_KEY')}


def upload_chunks(path, base, resource, repo):
    """Use Oxen's documented version upload protocol below gateway size limits."""
    content=path.read_bytes()
    version=xxhash.xxh128(content).hexdigest().lstrip('0') or '0'
    branch, destination=resource.split('/',1)
    directory, filename=destination.rsplit('/',1)
    workspace=str(uuid.uuid5(uuid.NAMESPACE_URL, base+'/'+version))
    response=requests.put(base+'/workspaces/get_or_create',headers=headers(),
                          json={'branch_name':branch,'workspace_id':workspace,'name':'genjustsu-'+version},timeout=30)
    response.raise_for_status()
    workspace=response.json()['workspace']['id']
    version_base=base+'/versions/'+version
    response=requests.post(version_base+'/create',headers=headers(),
                           json={'hash':version,'file_name':filename,'size':len(content),'dst_dir':directory},timeout=30)
    response.raise_for_status()
    chunk_size=1024*1024
    count=0
    for offset in range(0,len(content),chunk_size):
        response=requests.put(version_base+'/chunks',headers={**headers(),'Content-Type':'application/octet-stream'},
                              params={'offset':offset},data=content[offset:offset+chunk_size],timeout=120)
        response.raise_for_status()
        count+=1
    response=requests.post(version_base+'/complete',headers=headers(),json={
        'files':[{'hash':version,'file_name':filename,'dst_dir':directory,'num_chunks':count}],
        'workspace_id':workspace},timeout=120)
    response.raise_for_status()
    response=requests.post(base+'/workspaces/'+workspace+'/merge/'+quote(branch,safe=''),headers=headers(),
                           json={'message':'Genjustsu generation input','author':repo['latest_commit']['author'],
                                 'email':repo['latest_commit']['email']},timeout=120)
    response.raise_for_status()


def upload_file(path):
    path = Path(path)
    repository = setting('OXEN_STORAGE_REPO')
    if not re.fullmatch(r'[\w-]+/[\w.-]+', repository):
        raise MediaLinkError('Configure a private Oxen storage repository before generating.')
    base = API + '/repos/' + repository
    response = requests.get(base, headers=headers(), timeout=30)
    response.raise_for_status()
    repo = response.json()['repository']
    if repo.get('is_public') is not False or repo.get('visibility') != 'private':
        raise MediaLinkError('Oxen media storage must be private. No generation submitted.')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cache = path.with_name(path.name + '.oxen-storage.json')
    saved = json.loads(cache.read_text()) if cache.exists() else {}
    resource = saved.get('resource') if saved.get('sha256') == digest and saved.get('repository') == repository else None
    if resource and time.time()-saved.get('verified_at',0)<300:
        cached=saved.get('url','')
        parsed=urlparse(cached)
        expiry=parse_qs(parsed.query).get('oxen_expires',['0'])[0]
        if parsed.scheme=='https' and parsed.hostname=='hub.oxen.ai' and expiry.isdigit() and int(expiry)>time.time()+3600:
            return cached
    if not resource:
        branch = repo.get('default_branch') or 'main'
        resource = branch + '/genjustsu/' + digest + path.suffix.lower()
    encoded = quote(resource, safe='/')
    signed_endpoint = base + '/file/presigned_url/' + encoded
    # Signing accepts paths that do not yet exist, so probe the file itself.
    with requests.get(base + '/file/' + encoded, headers={**headers(), 'Range': 'bytes=0-0'},
                      stream=True, timeout=30) as probe:
        missing = probe.status_code == 404
        if not missing:
            probe.raise_for_status()
    if missing:
        if path.stat().st_size > 1024*1024:
            upload_chunks(path,base,resource,repo)
        else:
            content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
            with path.open('rb') as source:
                response = requests.put(base + '/file/' + encoded, headers=headers(),
                                        files={'file': (path.name, source, content_type)},
                                        data={'message': 'Genjustsu generation input',
                                              'name': repo['latest_commit']['author'],
                                              'email': repo['latest_commit']['email']}, timeout=120)
            response.raise_for_status()
    response = requests.get(signed_endpoint, headers=headers(), timeout=30)
    response.raise_for_status()
    # The same endpoint used by Oxen's native Workbench media preview.
    url = response.json().get('url')
    if not isinstance(url, str) or urlparse(url).scheme != 'https' or urlparse(url).hostname != 'hub.oxen.ai':
        raise MediaLinkError('Oxen did not return its expected signed HTTPS media link.')
    # Verify exact bytes without credentials: this is what the model will fetch.
    actual = hashlib.sha256()
    with requests.get(url, stream=True, timeout=120) as media:
        if media.status_code != 200 or 'json' in media.headers.get('Content-Type', '').lower():
            raise MediaLinkError('Oxen cannot read the signed media link. No generation submitted.')
        for chunk in media.iter_content(1024 * 1024):
            actual.update(chunk)
    if actual.hexdigest() != digest:
        raise MediaLinkError('The signed media download differs from the reviewed input.')
    cache.write_text(json.dumps({'repository': repository, 'resource': resource, 'sha256': digest,
                                'url':url,'verified_at':time.time()}))
    return url
