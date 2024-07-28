import openai
from . import schemas, models
from openai import OpenAI
import sqlite3
class GPT:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        self.client = OpenAI(api_key=self.openai_api_key)
        self.model="gpt-3.5-turbo"
        self.limit_sql_error = 5
    
    def generate_database_description(self, columns : dict[list[str]]) -> str:
        columns_info = """"""
        for column in columns:
            columns_info += f"\n- Table {column}: {", ".join(columns[column])}."

        template = f"""
        I have database with {len(columns)} tables:
        {columns_info}
        Provide descriptions of the relationships between tables to prepare for creating effective SQL queries to answer user questions. Just provide the descriptions of the relationships, dont explain anything.
        """
        context = {
            'role': 'system',
            'content': template}
        #Call gpt api
        relationship_info =  self.client.chat.completions.create(
                model= self.model,
                messages=[context],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )

        machine_description = f"""
        Database with {len(columns)} tables:
        {columns_info}
        Relationships between tables: \n
        {relationship_info.choices[0].message.content}
        """
        return machine_description
    
    def init_context(self, database: schemas.Database, message_history: list[models.Message]):
        self.message_history = []
        for message in message_history:
            self.message_history.append({
                "role": message.Role,
                "content": message.Content
            })
        self.database = database
        self.connection = sqlite3.connect(database.SavePath)
        self.cursor = self.connection.cursor()
        system_template = """You are an expert in SQLite. Based on the provided database description and additional notes, you will create appropriate SQL queries to answer user questions."""
        database_info = f"""
        You are an expert in SQLite. Based on the provided database description and additional notes, you will create appropriate SQL queries to answer user questions.
        Database description:
        {database.MachineDescription}
        Additional notes about the database:
        {database.UserDescription}
        """
        
        self.context = [{ 'role': 'system', 'content': system_template},
                        { 'role': 'user', 'content': database_info}]
        self.produce_response_context = { 'role': 'system', 'content': """You are an assistant skilled in generating precise answers to questions based on information stored in a database. Users will provide a question, an SQL query, and the results of that SQL query. Use this data to formulate a clear and concise answer to the question, ensuring your response is relevant and to the point."""}
        self.sql_request_template = """
        Here is the question:
        {content}
        Please give me SQLite query to answer the question based on the provided database. 
        Please provide the SQLite query as a string without any special characters at the beginning and end so that it can be used directly.
        Only provide the query, dont explain anything.
        If the question is not related to the database, please respond with "I don't know."
        """
        self.response_context = { 'role': 'system', 'content': """You are an assistant skilled in generating precise answers to questions based on information stored in a database. Users will provide a question, an SQL query, and the results of that SQL query. Use this data to formulate a clear and concise answer to the question, ensuring your response is relevant and to the point."""}
        self.response_template = """
        QUESTION: {content} \n
        SQL QUERY: {sqlite_query} \n
        RESULTS: {sqlite_result} \n
        Use this data to formulate a clear and concise answer to the question, ensuring your response is relevant and to the point.
        """

    def generate_response(self, new_message: schemas.MessageCreate):
        count_error = 0
        # sqlite_query_processed = None
        sqlite_result = None
        while count_error < self.limit_sql_error:
            print("count_error = ", count_error)
            try:
                sqlite_query = self.client.chat.completions.create(
                        model= self.model,
                        messages= self.context + [{"role": "user", "content": self.sql_request_template.format(content = new_message.Content)}], 
                        max_tokens=150,
                        n=1,
                        stop=None,
                        temperature=0.7,
                    )
                # sqlite_ = sqlite_query.choices[0].message.content
                # sqlite_ = sqlite_.replace("\n", " ") #remove new line
                # start_index =  sqlite_.find("```sql") + 6
                # end_index = sqlite_.find(";```")+1
                sqlite_query_processed = sqlite_query.choices[0].message.content
                sqlite_query_processed = sqlite_query_processed.replace("\n", " ")
                print(sqlite_query)
                self.cursor.execute(sqlite_query_processed)
                sqlite_result = str(self.cursor.fetchall())
                print(sqlite_result)
                # formatted_results = ''
                # for row in sqlite_result:
                #     formatted_results += ", ".join(str(item) for item in row) + "\n"
                # sqlite_result = formatted_results
                break
            except Exception as e:
                print(e)
                count_error += 1


        if count_error == self.limit_sql_error:
            sqlite_query_processed = "I don't know"
            sqlite_result = "I don't know"

        new_message_dict = {
            "role": 'user',
            "content": self.response_template.format(content = new_message.Content, sqlite_query = sqlite_query_processed, sqlite_result = sqlite_result)
        }
        print(new_message_dict)
        self.message_history.append(new_message_dict)
        response = self.client.chat.completions.create(
                model= self.model,
                messages=[self.response_context] + self.message_history + [new_message_dict],
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
                stream=True
            )
        return response
    
    def update_message_history(self, index: int = None, bot_message : schemas.MessageCreate = None):
        if index is not None:
            self.message_history = self.message_history[:index]
        if bot_message is not None:
            self.message_history.append({
                "role": bot_message.Role,
                "content": bot_message.Content
            })