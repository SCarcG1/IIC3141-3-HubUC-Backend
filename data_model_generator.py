'''
Run this script to generate a data model diagram for the specified SQLAlchemy models.
It requires the `sqlalchemy_data_model_visualizer` package,
and Graphviz installed and available in the PATH.
'''


from sqlalchemy_data_model_visualizer import generate_data_model_diagram
from app.models.user import User


generate_data_model_diagram(
    models=[User],
    output_file="data_model_diagram",
    add_labels=False,
)
