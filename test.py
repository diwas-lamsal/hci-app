import speech_recognition as s_r
print(s_r.Microphone.list_microphone_names())

mic = s_r.Microphone(device_index=3)
print(mic.list_microphone_names())