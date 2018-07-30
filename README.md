# pyttsbroker
Simple TTS (Text-To-Speech) broker for Python

License: Apache License 2.0

Warning: Refer to TTS provider license for caching, storing, redistributing and playing audio files generated with TTS engine

The module contains providers for:

 * Google Cloud TTS (commercial version, requires cloud service account key)
 * Amazon Polly (commercial version, requires API keys)
 
Usage example:
 
 ```python
from ttsbroker import TTSEngine as TE

e = TE( 
    cache_dir='/opt/workstuff/cache/gcloud',
    cache_format='ogg',
    device=0,
    gain=0,
    provider='gcloud')
    
e.say('test number one', gain=2)
e.say('test number two', provider_options={ 'voice': 'en-US-Wavenet-E' })
```
