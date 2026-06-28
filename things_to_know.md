### 1) related to Local LLM:
- now the model I used is `raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF`. You can find this model in the hugging face. For some knowledge, I've not just used some simple qwen2.5-7 billion parameter model, i've used 4-bit quantized version of it. Quantization is a process of shrinking the model's less important layer's weights to a lesser number of bit, means, to 4bit. There is some more info relate to this which geos a bit deep into deep learning. which you can find online.
- now lets know how, I used this model run locally.
#### llama.cpp:
- It's like a piece of software or its like a some box which takes something inside and makes some tweaks to it and let it work more efficiently. let me guide you thorough the process:
1) go to git hub, if you search this `llama.cpp`, you'll get some repo, and from there you need to downloads the latest version of it. you'll 
2) you'll see a folder got downloaded into your system, open that folder.
3) with that folder path open the cmd prompt. for example: it may look something like: `D:\llama` this llama is the folder which gets installed, and i stored that folder in my d drive, you may have another too, no worries.
4) now after getting the cmd prompt, you need to type a command there, which is available in the page of that git repo, but i'll tell you mine to get this model.
```bash
.\llama-server.exe -hf raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF -ngl 25
``` 
> Note: this command work only with models available in the hugging face, as this command contains the term 'hf'. if you want to change the model,  replace this: 'raaedk/Qwen2.5-7B-Instruct-Q4_K_M-GGUF' with any other model available on hugging face. 
5) wait for some time, there will be some process going on, then you'll see the model exposed to some port, by default its 8080. 
6) for testing purpose you can ctrl+click on that link, you'll see a webpage naming llama.cpp. you'll see a chat box to enter query. all set, we'll use that model in the project to structure the final response.

### 2) related to the qroq llm provider, model used and rate limiting.
- Now, see these days getting a well knowledge model for free is easy if you are just working with it for some time, so I choose this qroq llm provider, for my use case.
- and the reason to get that provider is, the model ive choose to use, which is some llama model, which is only available in that llm provider at that time, so I choose that.
#### why to take that specific model:
- I'll try not to go much deeper about this and explain you in simple terms.
- the main motive of this project is using `knowledge graphs (KG)`, in simple terms instead of only capturing semantic info and keyword info, this KG captures entities and relations of the data, which stands out as priority when you got some complex queries including, gathering info from different sources and understanding complex relations in data and query.
- and now for this process to make possible we need to build graphs, which will be explained in different script, but now, to build that graph based on our data, we need some llm model which has good knowledge, understand data well and extract entities and relations from data. 
- now in the process of searching free models, I got to know about this model and its free in this qroq llm provider.
- so thats all the reason to go with this model specifically.
- all the info related to that graph building, the whole concept of that graphs will be listed in another file.
#### why not local model to build graph.
- 