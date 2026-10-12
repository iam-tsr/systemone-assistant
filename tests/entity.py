from src.entity_recognition import extract_entity, fast_entity_recon
from src.pipeline import _extract_query_entities

query = [{'HumanMessage': 'I want to change my address for order 12345 to 456 New Street, New City.', 'AIMessage': 'I can help you with that.'}, {'HumanMessage': 'I want to cancel my order 67890 and get a refund.'}]

output = _extract_query_entities(query)
print(output.get("order_id"))

# output = fast_entity_recon(query)
# print(output) # 85% confidence need to verify the output.