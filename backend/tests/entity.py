from src.entity_recognition import extract_entity, fast_entity_recon

query = [{'HumanMessage': 'I want to know about my order one triple zero one.'}]

output = fast_entity_recon(query)
print(output) # 85% confidence need to verify the output.

output = extract_entity(query)
print(output)