import google.generativeai as genai
genai.configure(api_key="AIzaSyAioHMR96CVLWhOX-xfQl9tI-eLrhtCXkM")

models = genai.list_models()
for m in models:
    print(m.name)
