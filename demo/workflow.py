WORKFLOW_STEPS = [
    {"status": "payment", "next": "parking", "required_files": ["payment_doc"]},
    {"status": "parking", "next": "preparation", "required_files": ["parking_doc"]},
    {"status": "preparation", "next": "bill_of_lading", "required_files": ["preparation_doc"]},
    {"status": "bill_of_lading", "next": "port_transport", "required_files": ["bill_of_lading_doc"]},
    {"status": "port_transport", "next": "port_arrival", "required_files": ["port_transport_doc"]},
    {"status": "port_arrival", "next": "order_received", "required_files": ["port_arrival_doc"]},
    {"status": "order_received", "next": None, "required_files": ["order_received_doc"]},
]