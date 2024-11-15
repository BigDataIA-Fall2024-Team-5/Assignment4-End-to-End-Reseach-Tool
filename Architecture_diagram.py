from diagrams import Diagram, Cluster
from diagrams.onprem.workflow import Airflow
from diagrams.custom import Custom
from diagrams.aws.storage import S3
from diagrams.onprem.client import User
from diagrams.aws.database import RDS

with Diagram("End-to-End Research Tool Architecture", show=False):
    user = User("Researcher")

    with Cluster("Airflow Pipeline"):
        airflow = Airflow("Airflow Orchestrator")
        
        with Cluster("Data Collection and Processing"):
            scraper = Custom("CFA Website Scraper", "./icons/cfa.png")
            s3 = S3("S3 Storage")
            snowflake = Custom("Snowflake", "./icons/Snowflake.png")
            pdf_processor = Custom("Dockling", "./icons/dockling.png")
            pinecone = Custom("Pinecone Vector DB", "./icons/pinecone_logo.png")
            embed = Custom("Nvidia Embedding Model", "./icons/nvidia_emb.png")
        airflow >> scraper >> s3
        airflow >> s3 >> snowflake
        airflow >> snowflake >> pdf_processor >> embed >> pinecone

    with Cluster("Research Agents"):
        langraph = Custom("Langraph", "./icons/langraph_logo.png")
        arxiv_agent = Custom("Arxiv Agent", "./icons/arxiv.png")
        web_agent = Custom("Web Search Agent", "./icons/web_agent.png")
        rag_agent = Custom("RAG Agent", "./icons/rag.png")

    with Cluster("User Interface"):
        interface = Custom("Coagent", "./icons/coagent.png")
        pdf_export = Custom("PDF Export", "./icons/pdf_logo.png")
        codelabs_export = Custom("Codelabs Export", "./icons/codelabs_logo.png")

    # Data flow
    pinecone >> langraph >> [arxiv_agent, web_agent, rag_agent]
    langraph >> interface
    interface >> [pdf_export, codelabs_export]

    user >> interface