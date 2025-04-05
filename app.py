import io
import streamlit as st
import numpy as np
import plotly.graph_objects as go

def generate_bolt_input(head_diameter, head_thickness, shank_diameter, shank_length, element_size):
    output = io.StringIO()
    output.write("** Abaqus Input File for 3D Bolt Model\n")
    output.write("*Heading\n")
    output.write("3D Bolt Model\n\n")
    output.write("*Part, name=Bolt\n")
    output.write("*Node\n")
    
    head_radius = head_diameter / 2
    shank_radius = shank_diameter / 2
    
    num_circumferential = max(8, int((np.pi * max(head_diameter, shank_diameter)) / element_size))
    num_head_layers = max(1, int(head_thickness / element_size))
    num_shank_layers = max(1, int(shank_length / element_size))
    
    node_id = 1
    nodes = {}
    node_coords = []

    # Bolt head generation
    for layer in range(num_head_layers + 1):
        z = head_thickness - (layer / num_head_layers) * head_thickness
        for i in range(num_circumferential + 1):
            theta = (i / num_circumferential) * 2 * np.pi
            for r in range(int(head_radius / element_size) + 1):
                radius = min(r * element_size, head_radius)
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                output.write(f"{node_id}, {x:.3f}, {y:.3f}, {z:.3f}\n")
                nodes[(layer, i, r)] = node_id
                node_coords.append((x, y, z))
                node_id += 1

    # Corrected shank generation
    for length_layer in range(num_shank_layers + 1):
        z = head_thickness - (length_layer * (shank_length / num_shank_layers))
        for i in range(num_circumferential + 1):
            theta = (i / num_circumferential) * 2 * np.pi
            for r in range(int(shank_radius / element_size) + 1):
                radius = min(r * element_size, shank_radius)
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                output.write(f"{node_id}, {x:.3f}, {y:.3f}, {z:.3f}\n")
                nodes[('shank', length_layer, i, r)] = node_id
                node_coords.append((x, y, z))
                node_id += 1

    # Element generation
    output.write("*Element, type=C3D8\n")
    elem_id = 1
    
    # Head elements
    for layer in range(num_head_layers):
        for i in range(num_circumferential):
            for r in range(int(head_radius / element_size)):
                n = [
                    nodes[(layer, i, r)],
                    nodes[(layer, i+1, r)],
                    nodes[(layer, i+1, r+1)],
                    nodes[(layer, i, r+1)],
                    nodes[(layer+1, i, r)],
                    nodes[(layer+1, i+1, r)],
                    nodes[(layer+1, i+1, r+1)],
                    nodes[(layer+1, i, r+1)]
                ]
                output.write(f"{elem_id}, " + ", ".join(map(str, n)) + "\n")
                elem_id += 1

    # Shank elements
    for layer in range(num_shank_layers):
        for i in range(num_circumferential):
            for r in range(int(shank_radius / element_size)):
                n = [
                    nodes[('shank', layer, i, r)],
                    nodes[('shank', layer, i+1, r)],
                    nodes[('shank', layer, i+1, r+1)],
                    nodes[('shank', layer, i, r+1)],
                    nodes[('shank', layer+1, i, r)],
                    nodes[('shank', layer+1, i+1, r)],
                    nodes[('shank', layer+1, i+1, r+1)],
                    nodes[('shank', layer+1, i, r+1)]
                ]
                output.write(f"{elem_id}, " + ", ".join(map(str, n)) + "\n")
                elem_id += 1

    # Complete INP file
    output.write("*End Part\n")
    output.write("*Material, name=Steel\n*Elastic\n210000, 0.3\n")
    output.write("*Solid Section, elset=ALL_ELEMENTS, material=Steel\n")
    output.write("*Assembly, name=Assembly\n*Instance, part=Bolt\n*End Instance\n*End Assembly\n")
    output.write("*Step, name=StaticStep\n*Static\n1.0, 1.0\n*End Step")
    
    content = output.getvalue()
    return content, io.BytesIO(content.encode()), node_coords

def visualize_bolt(node_coords):
    fig = go.Figure()
    if node_coords:
        x, y, z = zip(*node_coords)
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(size=2, color=z, colorscale='Viridis')
        ))
    fig.update_layout(
        scene=dict(
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            aspectmode='data'
        ),
        height=600,
        margin=dict(l=0, r=0, b=0, t=30)
    )
    return fig

# Streamlit UI
st.title("3D Bolt Generator for Abaqus")
st.sidebar.header("Design Parameters")

hd = st.sidebar.number_input("Head Diameter (mm)", 10.0, 50.0, 20.0)
ht = st.sidebar.number_input("Head Thickness (mm)", 2.0, 20.0, 8.0)
sd = st.sidebar.number_input("Shank Diameter (mm)", 5.0, 30.0, 12.0)
sl = st.sidebar.number_input("Shank Length (mm)", 10.0, 100.0, 40.0)
es = st.sidebar.number_input("Element Size (mm)", 0.5, 5.0, 2.0)

if st.sidebar.button("Generate Model"):
    with st.spinner("Creating 3D Bolt..."):
        inp_content, inp_file, nodes = generate_bolt_input(hd, ht, sd, sl, es)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Abaqus Input File")
            st.download_button(
                "Download INP File",
                data=inp_file,
                file_name="bolt_model.inp",
                mime="text/plain"
            )
            st.code(inp_content, language='python')
        
        with col2:
            st.subheader("3D Preview")
            st.plotly_chart(visualize_bolt(nodes), use_container_width=True)
        
        st.success(f"Generated bolt with total length: {ht + sl:.1f}mm")
else:
    st.info("Configure parameters and click 'Generate Model'")
