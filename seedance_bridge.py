"""Provider routing. Saved jobs use the provider that originally accepted them."""
from config import setting

def adapter(provider):
    if provider=='oxen':
        import oxen_seedance
        return oxen_seedance
    if provider=='lec':
        import lec_seedance
        return lec_seedance
    if provider=='replicate':
        import replicate_seedance
        return replicate_seedance
    raise ValueError('Unsupported legacy provider. Saved files are preserved; do not resubmit automatically.')

def submit(folder,prompt,sirio,tein=None,status=print):
    return adapter(setting('GENERATION_PROVIDER','oxen')).submit(folder,prompt,sirio,tein,status)

def wait_and_finish(folder,request_id,status=print):
    from replicate_seedance import saved_provider
    return adapter(saved_provider(folder)).wait_and_finish(folder,request_id,status)

def submit_hd(folder):
    from replicate_seedance import saved_provider
    provider=saved_provider(folder)
    if provider=='lec':raise ValueError('This model generates 720p and has no HD upgrade.')
    return adapter(provider).submit_hd(folder)
