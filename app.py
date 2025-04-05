import io
import streamlit as st
import numpy as np
import plotly.graph_objects as go

def generate_bolt_input(head_diameter, head_thickness, shank_diameter, shank_length, thread_length, element_size):
    # Initialize output buffer
    output = io.StringIO()
    output.write("** Abaqus Input File for 3D Bolt Model\n")
    output.write("*Heading\n")
    output.write("3D Bolt Model\n\n")
    output.write("*Part, name=Bolt\n")
    output.write("*Node\n")
    
    # Parameters
    head_radius = head_diameter / 2
    shank_radius = shank_diameter / 2
    
    # Calculate number of elements
    num_circumferential_elements = max(8, int((np.pi * max(head_diameter, shank_diameter)) / element_size))
    num_head_thickness_elements = max(1, int(head_thickness / element_size))
    num_shank_length_elements = max(1, int(shank_length / element_size))
    
    # Initialize node tracking
    node_id = 1
    nodes = {}
    node_coordinates = []
    
    # Generate nodes for bolt head (top surface)
    for i in range(num_circumferential_elements + 1):
        theta = (i / num_circumferential_elements) * 2 * np.pi
        
        # Create nodes from center to edge of bolt head (top face)
        for r in range(int(head_radius / element_size) + 1):
            radius = r * element_size if r < int(head_radius / element_size) else head_radius
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)
            z = head_thickness
            
            output.write(f"{node_id}, {x:.3f}, {y:.3f}, {z:.3f}\n")
            nodes[(0, i, r)] = node_id
            node_coordinates.append((x, y, z))
            node_id += 1
    
    # Generate nodes for bolt head (layers)
    for layer in range(1, num_head_thickness_elements + 1):
        z = head_thickness - (layer / num_head_thickness_elements) * head_thickness
        
        for i in range(num_circumferential_elements + 1):
            theta = (i / num_circumferential_elements) * 2 * np.pi
            
            # Create nodes from center to edge of bolt head
            for r in range(int(head_radius / element_size) + 1):
                radius = r * element_size if r < int(head_radius / element_size) else head_radius
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                
                output.write(f"{node_id}, {x:.3f}, {y:.3f}, {z:.3f}\n")
                nodes[(layer, i, r)] = node_id
                node_coordinates.append((x, y, z))
                node_id += 1
    
    # Generate nodes for bolt shank
    for layer in range(num_shank_length_elements + 1):
        z = -layer * (shank_length / num_shank_length_elements)
        
        for i in range(num_circumferential_elements + 1):
            theta = (i / num_circumferential_elements) * 2 * np.pi
            
            # Create nodes for shank (only on the surface for visualization simplicity)
            x = shank_radius * np.cos(theta)
            y = shank_radius * np.sin(theta)
            
            output.write(f"{node_id}, {x:.3f}, {y:.3f}, {z:.3f}\n")
            nodes[(layer + num_head_thickness_elements, i, 0)] = node_id
            node_coordinates.append((x, y, z))
            node_id += 1
    
    # Elements - simplified for visualization
    output.write("*Element, type=C3D8\n")
    element_id = 1
    
    # Elements for bolt head (simplified)
    for layer in range(num_head_thickness_elements):
        for i in range(num_circumferential_elements):
            for r in range(int(head_radius / element_size)):
                # Define the 8 nodes of each hexahedral element
                n1 = nodes.get((layer, i, r), 1)
                n2 = nodes.get((layer, i+1, r), 1)
                n3 = nodes.get((layer, i+1, r+1), 1)
                n4 = nodes.get((layer, i, r+1), 1)
                n5 = nodes.get((layer+1, i, r), 1)
                n6 = nodes.get((layer+1, i+1, r), 1)
                n7 = nodes.get((layer+1, i+1, r+1), 1)
                n8 = nodes.get((layer+1, i, r+1), 1)
                
                output.write(f"{element_id}, {n1}, {n2}, {n3}, {n4}, {n5}, {n6}, {n7}, {n8}\n")
                element_id += 1
    
    # Elements for bolt shank (simplified)
    for layer in range(num_shank_length_elements):
        for i in range(num_circumferential_elements):
            # Define simplified cylindrical elements
            n1 = nodes.get((layer + num_head_thickness_elements, i, 0), 1)
            n2 = nodes.get((layer + num_head_thickness_elements, i+1, 0), 1)
            n3 = nodes.get((layer + num_head_thickness_elements + 1, i+1, 0), 1)
            n4 = nodes.get((layer + num_head_thickness_elements + 1, i, 0), 1)
            
            output.write(f"{element_id}, {n1}, {n2}, {n3}, {n4}, {n1}, {n2}, {n3}, {n4}\n")
            element_id += 1
    
    # Complete the Abaqus input file
    output.write("*End Part\n\n")
    output.write("*Material, name=Steel\n")
    output.write("*Elastic\n")
    output.write(f"210000, 0.3\n\n")
    output.write("*Solid Section, elset=ALL_ELEMENTS, material=Steel\n")
    output.write("*Assembly, name=Assembly\n")
    output.write("*Instance, name=Bolt-1, part=Bolt\n")
    output.write("*End Instance\n")
    output.write("*End Assembly\n\n")
    output.write("*Step, name=StaticStep, nlgeom=YES\n")
    output.write("*Static\n")
    output.write("1.0, 1.0, 1e-05, 1.0\n\n")
    output.write("*End Step\n")
    
    inp_content = output.getvalue()
    output.seek(0)
    byte_data = io.BytesIO(inp_content.encode('utf-8')).getvalue()
    
    return inp_content, byte_data, node_coordinates

def visualize_bolt(node_coordinates, head_diameter, head_thickness, shank_diameter, shank_length):
    # Extract coordinates
    x_vals, y_vals, z_vals = zip(*node_coordinates)
    
    # Create the figure
    fig = go.Figure()
    
    # Add points for the nodes
    fig.add_trace(go.Scatter3d(
        x=x_vals, y=y_vals, z=z_vals,
        mode='markers',
        marker=dict(
            size=2,
            color=z_vals,
            colorscale='Viridis',
        ),
        showlegend=False
    ))
    
    # Create bolt head cylinder
    head_radius = head_diameter / 2
    theta = np.linspace(0, 2*np.pi, 36)
    z_head = np.linspace(0, head_thickness, 10)
    theta_grid, z_grid = np.meshgrid(theta, z_head)
    
    x_head = head_radius * np.cos(theta_grid)
    y_head = head_radius * np.sin(theta_grid)
    
    fig.add_trace(go.Surface(
        x=x_head, y=y_head, z=z_grid,
        colorscale='Blues',
        opacity=0.7,
        showscale=False,
        name="Bolt Head"
    ))
    
    # Create bolt top face
    r = np.linspace(0, head_radius, 10)
    theta = np.linspace(0, 2*np.pi, 36)
    r_grid, theta_grid = np.meshgrid(r, theta)
    
    x_top = r_grid * np.cos(theta_grid)
    y_top = r_grid * np.sin(theta_grid)
    z_top = np.ones_like(x_top) * head_thickness
    
    fig.add_trace(go.Surface(
        x=x_top, y=y_top, z=z_top,
        colorscale='Blues',
        opacity=0.8,
        showscale=False,
        name="Bolt Top"
    ))
    
    # Create bolt shank
    shank_radius = shank_diameter / 2
    theta = np.linspace(0, 2*np.pi, 36)
    z_shank = np.linspace(0, -shank_length, 20)
    theta_grid, z_grid = np.meshgrid(theta, z_shank)
    
    x_shank = shank_radius * np.cos(theta_grid)
    y_shank = shank_radius * np.sin(theta_grid)
    
    fig.add_trace(go.Surface(
        x=x_shank, y=y_shank, z=z_grid,
        colorscale='Greys',
        opacity=0.7,
        showscale=False,
        name="Bolt Shank"
    ))
    
    # Add threads visualization (simplified)
    if thread_length > 0:
        thread_start = -shank_length + thread_length
        z_thread = np.linspace(thread_start, -shank_length, 50)
        
        # Create a spiral
        theta_thread = np.linspace(0, 10*np.pi, 100)
        x_thread = []
        y_thread = []
        z_thread = []
        
        for t in theta_thread:
            x_thread.append(shank_radius * np.cos(t))
            y_thread.append(shank_radius * np.sin(t))
            z_thread.append(thread_start - (t / (10*np.pi)) * thread_length)
        
        fig.add_trace(go.Scatter3d(
            x=x_thread, y=y_thread, z=z_thread,
            mode='lines',
            line=dict(color='black', width=4),
            name="Threads"
        ))
    
    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis_title="X",
            yaxis_title="Y",
            zaxis_title="Z",
            aspectmode='data'
        ),
        height=600,
        width=700,
        margin=dict(l=0, r=0, b=0, t=40),
    )
    
    return fig

# Streamlit UI
st.title("3D Bolt Generator for Abaqus :wrench:")
st.write("Generate a 3D bolt model for Abaqus simulation")

# Sidebar for user inputs
st.sidebar.header("Bolt Parameters")
head_diameter = st.sidebar.number_input("Bolt Head Diameter (mm)", value=20.0, min_value=5.0)
head_thickness = st.sidebar.number_input("Bolt Head Thickness (mm)", value=8.0, min_value=1.0)
shank_diameter = st.sidebar.number_input("Shank Diameter (mm)", value=12.0, min_value=3.0)
shank_length = st.sidebar.number_input("Shank Length (mm)", value=40.0, min_value=5.0)
thread_length = st.sidebar.number_input("Thread Length (mm)", value=25.0, min_value=0.0)
element_size = st.sidebar.number_input("Element Size (mm)", value=2.0, min_value=0.5)

# Generate Abaqus input file
if st.sidebar.button("Generate Bolt Model"):
    with st.spinner("Generating 3D bolt model..."):
        inp_content, inp_file, node_coordinates = generate_bolt_input(
            head_diameter, head_thickness, shank_diameter, shank_length, thread_length, element_size
        )

        col1, col2 = st.columns([1, 1])  # Equal width columns

        with col1:
            st.subheader("Generated Abaqus Input File")
            st.text_area("Abaqus Input File:", inp_content, height=600)
            st.download_button(
                label="Download Abaqus Input File",
                data=inp_file,
                file_name="bolt.inp",
                mime="text/plain"
            )

        with col2:
            st.subheader("Bolt Visualization")
            fig = visualize_bolt(node_coordinates, head_diameter, head_thickness, shank_diameter, shank_length)
            st.plotly_chart(fig)

        # Display bolt specifications
        st.subheader("Bolt Specifications")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Head Diameter", f"{head_diameter} mm")
            st.metric("Head Thickness", f"{head_thickness} mm")
            st.metric("Shank Diameter", f"{shank_diameter} mm")
        with col2:
            st.metric("Shank Length", f"{shank_length} mm")
            st.metric("Thread Length", f"{thread_length} mm")
            st.metric("Total Length", f"{head_thickness + shank_length} mm")

        st.success("3D bolt model generated successfully!")
else:
    # Show sample visualization when app first loads
    st.subheader("Bolt Visualization Preview")
    sample_nodes = [(0, 0, 0)]  # Placeholder
    fig = visualize_bolt(sample_nodes, 20.0, 8.0, 12.0, 40.0)
    st.plotly_chart(fig)
    st.info("Click 'Generate Bolt Model' to create the Abaqus input file.")