from src.entity_recognition import extract_entity, fast_entity_recon

query = [{'HumanMessage': 'I want to change the shipping address for my order one zero zero zero one to one Test St, Mumbai, Maharashtra double one double zero two.'}]

output = fast_entity_recon(query)
print(output) # 85% confidence need to verify the output.

output = extract_entity(query)
print(output)