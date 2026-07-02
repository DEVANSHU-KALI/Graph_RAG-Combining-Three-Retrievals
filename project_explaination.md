### what is this project.
- I've mentioned about the project in readme file simply, but to go more deeper, I got some more information.
- lets go one by one, so lets start with semantic retrieval.
#### 1) **semantic retrieval**: 
- In simple words it just about understanding data semantically. And at the time we try to retrieve data from the database, we do the same thing to the query too, understand that query semantically, see for relevant information in the database and retrieve that data to generate response.
- under the hood, this semantical understanding works on embeddings, data is converted into embeddings, internally that data is mapped into a vector space based on these embeddings. data related to each other get closer and other stay far. In this way embeddings works.
- embedding are nothing but some value, which is a coordinate in that vector space. And when we call embeddings, there are some tons of values representing the sentence's meaning through that coordinates. Each value of that list represents some semantic feature. 
- now that info conversion into embeddings is done using embedding models, for this project i've used some `all-mpnet-base-v2` which comes with 768D (dimensions), and that thing 768D means whatever you send to the model for conversion will be converted into a list of 768 values, where some values are negative and some positive. 
- Now to where to store that embeddings, which becomes a question here, not all places in your computer can store these embeddings, there got some different databases, where I went with `qdrant`, there are also different databases available, as this was simple, user friendly, better in security and also got some webpage to view the database.
- In ingestion stage, which is done only once, data is broke down into chunks (small pieces), converted into embeddings, and stored in the database with some metadata, including chunk text, chunk id mainly.
- while in the stage of passing query, the query is converted into embeddings again, compared with the stored embeddings, find some relevant chunks, and retrieve the chunks text. 
- In this single concept there are sub concepts again. chunking, embeddings, database to store embeddings, and one concept which is not that visible is that comparison between the query embeddings and store embeddings. all these will be explained in more detail.

#### 2) **keyword retrieval**:
- as we just got know about semantic retrieval, but the reason to also add this retrieval is important here. semantic understanding fails when there are rare keywords in the data and the system starts hallucinating. to avoid this issues we get this retrieval.
- the concept of keyword retrieval is possible by `bm25 index`, its a library which simply some information related to each word we got in the data, for example, we have a word 'red', bm25 index gets info like, how many times this is word is present in the data, all the file which has this word from the data, and some more. and store them on the ram at run time according to this project, or another way is to store that information in .pkl file and add that to run time when we are executing this project. 
- now when the system is on execution, the query is broke into tokens, done some comparision, like seeing which chunk has the most of the word which the query contains, how many time each word is present in that chunks, etc. based on this type of information, the bm25 index will give some score to the chunks, and later we sort the chunks based on that score and retrieve the top 3 chunks for that query.
- this was as simple explanation of how the keyword retrieval works generally.
- one point to mention here is, unlike the semantic retrieval or the graph retrieval we dont need a specific database to store the index or anything related keyword retrieval. to make this retrieval possible, we just need the bm25 index which makes some statistics and text corpus, which is simply the chunk text which is available in the qdrant database where we store the chunk text in each point, we just collect all that text into one place and do that work.

#### 3) **graph retrieval**:
- to make this graph retrieval possible we need a database, which is `neo4j`, one of the most trusted and used database to store the graphs, there are also some other but this is widely used.
- in simple words we build graphs which contains node (entities) which is some data and there will be the edges (relationships) which connects the nodes with some connection name. store them in the neo4j database. 
- there is a language called `cypher` for the neo4j database which is like `sql` for normal data. here there are two thing to remember, `entities` and `relationships`, when we build graphs we store both of these related to the data in the database.  
- when it comes to retrieval stage, we extract the entities from the query and search the database for the relationships using this cypher language.
- llm is used to extract that entities from the query when retrieval time. thats the reason why we tried to use a well knowledged model using the api from the `Qroq llm provider`. 

#### Reranker:
- these are models which check whether all the retrieved chunks are answer the query correctly or not!, and rerankes the chunks, which simply means filter the most relevant chunks to answer the query. 