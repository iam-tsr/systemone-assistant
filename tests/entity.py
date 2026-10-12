from src.entity_recognition import extract_entity, fast_entity_recon

query = "here it is 12345."

output = extract_entity(query)
print(output)

output = fast_entity_recon([query])
print(output) # 85% confidence need to verify the output.