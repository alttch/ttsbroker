# ttsbroker
Simple TTS (Text-To-Speech) broker for Python

License: Apache License 2.0

Warning: Refer to TTS provider license about caching, storing, redistributing
and playing rights for the audio files generated with TTS engine.

The module contains providers for:

 * gcloud: Google Cloud TTS (requires cloud service account key), requires
   oauth2client python module

 * polly: Amazon Polly (requires AWS API keys), requires boto3 python module

 * watson: IBM Watson (requires Watson service credentials)
 
Usage example:
 
```python
from ttsbroker import TTSEngine as TTSE

e = TTSE(
    cache_dir='/data/cache/gcloud',
    cache_format='ogg',
    device=0,
    gain=0,
    provider='gcloud')
e.set_key('client_service_key.json')    
e.say('test number one', gain=2)
e.say('test number two', provider_options={ 'voice': 'en-US-Wavenet-E' })
```

(c) 2018 Altertech Group, https://www.altertech.com/

