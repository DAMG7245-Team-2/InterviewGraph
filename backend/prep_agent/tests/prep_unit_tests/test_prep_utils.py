from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
import os
import pytest
from prep_agent.utils import search_pinecone


@pytest.mark.asyncio
async def test_search_pinecone():
    load_dotenv()
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.IndexAsyncio(host=os.getenv("PINECONE_HOST", ""))
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    query_list = [
        "To query PostgreSQL, you create the connection, execute the sql query using the\npandas read_sql() method, and then use the pandas to_csv() method to write\nthe data to disk:\n\n```\ndef queryPostgresql():\nconn_string=\"dbname='dataengineering' host='localhost'\nuser='postgres' password='postgres'\"\nconn=db.connect(conn_string)\ndf=pd.read_sql(\"select name,city from users\",conn)\ndf.to_csv('postgresqldata.csv')\nprint(\"-------Data Saved------\")\n```\n\n94 Working with Databases\n\nTo insert the data into Elasticsearch, you create the Elasticsearch object connecting\nto localhost. Then, read the CSV from the previous task into a DataFrame, iterate\nthrough the DataFrame, converting each row into JSON, and insert the data using the\nindex method:\n\n```\ndef insertElasticsearch():\nes = Elasticsearch()\ndf=pd.read_csv('postgresqldata.csv')\nfor i,r in df.iterrows():\ndoc=r.to_json()\nres=es.index(index=\"frompostgresql\",\ndoc_type=\"doc\",body=doc)\nprint(res)\n```\nNow you have a complete data pipeline in Airflow. In the next section, you will run it and\nview the results.\n\n**Running the DAG**\n\nTo run the DAG, you need to copy your code to your $AIRFLOW_HOME/dags folder.\nAfter moving the file, you can run the following commands:\n\n```\nairflow webserver\nairflow scheduler\n```\nWhen these commands complete, browse to [http://localhost:8080](http://localhost:8080) to see the\nAirflow GUI. Select **MyDBdag** , and then select **Tr e e Vi e w**. You can schedule five runs of\nthe DAG and click **Go**. As it runs, you should see the results underneath, as shown in the\nfollowing screenshot:"
    ]
    top_k = 1
    result = await search_pinecone(index, embeddings, query_list, top_k, 0.9)
    expected_result = (
        "Content from RAG:\n"
        + f"{'=' * 80}\n"
        + "Source: DataEngineeringWithPython\n"
        + f"{'-' * 80}\n"
        + "Author: Paul Crickard\n===\n"
        + "Full source content limited to 4000 tokens: "
        + query_list[0][: 4000 * 4]
        + "\n\n"
        + f"{'=' * 80}\n\n"
    ).strip()
    assert result == expected_result
