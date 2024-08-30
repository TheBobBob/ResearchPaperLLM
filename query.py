
import paperscraper
import ollama

#implement a simple point blank understanding method (can take in a prompt that the user gives and splits it into two/multiple sets of querys like query_set_2/query_set_3)

#not mutually exclusive, all of them have to be included


query_set_1 = ['glioblastoma']
query_set_2 = ['cell']
query_set_3 = ['growth']
query = [query_set_1, query_set_2, query_set_3]

for item in query_set_1:
    var1 = query_set_1[0]

from paperscraper.arxiv import get_and_dump_arxiv_papers

get_and_dump_arxiv_papers(query, output_filepath=f'{var1}.jsonl', max_results = 1)

final_query_set_name = f'{var1}.jsonl'

print(final_query_set_name)

