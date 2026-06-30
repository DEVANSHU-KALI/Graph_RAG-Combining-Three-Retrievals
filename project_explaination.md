### what is this project.
- I've mentioned about the project in readme file simply, but to go more deeper, I got some more information.
- lets go one by one, so lets start with semantic retrieval.
#### 1) **semantic retrieval**: 
- In simple words it just about understanding data semantically. And at the time we try to retrieve data from the database, we do the same thing to the query too, understand that query semantically, see for relevant information in the database and retrieve that data to generate response.
- under the hood, this semantical understanding works on embeddings, data is converted into embeddings, internally that data is mapped into a vector space based on these embeddings. data related to each other get closer and other stay far. In this way embeddings works.
- embedding are nothing but some value, which is a coordinate in that vector space. And when we call embeddings, there are some tons of values representing the sentence's meaning through that coordinates. Each value of that list represents some semantic feature. 
- now that info conversion into embeddings is done using embedding models, for this project i've used some `all-mpnet-base-v2` which comes with 768D (dimensions), and that thing 768D means whatever you send to the model for conversion will be converted into a list of 768 values, where some values are negative and some positive. 