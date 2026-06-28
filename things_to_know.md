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
