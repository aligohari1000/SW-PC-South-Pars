import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from tensorflow.keras.models import load_model
import io
import matplotlib.pyplot as plt

st.title("Water Saturation Profile Prediction")

uploaded_file = st.file_uploader("Upload your well-logging Excel file", type=["xlsx"])

if uploaded_file is not None:
    st.subheader("Data Preprocessing")
    
    try:

        data = pd.read_excel(uploaded_file)
        st.write("Original Data Preview:")
        st.write(data.head())

        
        data = data.dropna(axis=1, how='all')
        st.write("Data after removing empty columns:")
        st.write(data.head())

        
        damping_factor = 0.6
        smoothed_data = data.copy()
        for column in data.select_dtypes(include=['float64', 'int64']).columns:  # فقط ستون‌های عددی
            smoothed_data[column] = smoothed_data[column].ewm(alpha=damping_factor).mean()
        
        st.write("Data after exponential smoothing:")
        st.write(smoothed_data.head())

       
        selected_features = ['zone', 'Depth', 'DTCO', 'NPHI', 'RHOB', 'RLA3', 'RLA5', 'SGR']
        if all(feature in smoothed_data.columns for feature in selected_features):
            selected_data = smoothed_data[selected_features]
            st.write("Selected Features:")
            st.write(selected_data.head())
        else:
            missing_features = [feature for feature in selected_features if feature not in smoothed_data.columns]
            st.error(f"The following features are missing in the data: {missing_features}")
            st.stop()

        
        st.subheader("Feature Engineering")
        
        
        selected_data['log(RLA3)'] = np.log(selected_data['RLA3'].replace(0, np.nan)).fillna(0)
        selected_data['log(RLA5)'] = np.log(selected_data['RLA5'].replace(0, np.nan)).fillna(0)
        selected_data.drop(columns=['RLA3', 'RLA5'], inplace=True)

        
        selected_data.insert(0, 'well number', 5)  
        selected_data.insert(1, 'abs depth', range(0, len(selected_data)))  

        
        final_columns = [
            'well number', 'abs depth', 'zone', 'Depth', 'DTCO', 
            'NPHI', 'RHOB', 'log(RLA3)', 'log(RLA5)', 'SGR'
        ]
        selected_data = selected_data[final_columns]
        
        st.write("Data after feature engineering:")
        st.write(selected_data.head())

        
        st.subheader("Feature Scaling")

        
        minmax_scaler = MinMaxScaler()
        minmax_scaled_data = pd.DataFrame(minmax_scaler.fit_transform(selected_data), columns=selected_data.columns)
        st.write("Data after MinMax Scaling:")
        st.write(minmax_scaled_data.head())

        
        standard_scaler = StandardScaler()
        standard_scaled_data = pd.DataFrame(standard_scaler.fit_transform(selected_data), columns=selected_data.columns)
        st.write("Data after Standard Scaling:")
        st.write(standard_scaled_data.head())

        
        reshaped_data = standard_scaled_data.values.reshape(standard_scaled_data.shape[0], standard_scaled_data.shape[1], 1)
        st.session_state["reshaped_data"] = reshaped_data 

        st.success("Feature engineering and scaling completed successfully!")

        
        model_path = "model_foldddd_1.keras"  
        try:
            model = load_model(model_path)
            st.success("Model loaded successfully!")
        except Exception as e:
            st.error(f"Error loading model: {e}")
            st.stop()

        
        st.subheader("Prediction Results")
        try:
            predictions = model.predict(reshaped_data)
            st.write("Predicted SW-PC values:")
            st.write(predictions)

            
            prediction_df = pd.DataFrame(predictions.flatten(), columns=["Predicted SW-PC"])
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                prediction_df.to_excel(writer, index=False, sheet_name="Predictions")
            st.download_button(
                label="Download Predictions as Excel",
                data=excel_buffer.getvalue(),
                file_name="SW-PC_Predictions.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            st.error(f"Error during prediction or saving results: {e}")

       
        st.subheader("Well Log Visualization")
        try:
            if "Depth" in selected_data.columns:
                st.write("Length of Depth:", len(selected_data["Depth"]))
                st.write("Length of Predictions:", len(predictions.flatten()))

                
                min_length = min(len(selected_data["Depth"]), len(predictions.flatten()))
                depth = selected_data["Depth"].iloc[:min_length] 
                predicted_sw_pc = predictions.flatten()[:min_length]  

                
                fig, ax = plt.subplots(figsize=(8, 10))
                ax.plot(predicted_sw_pc, depth, label="Predicted SW-PC", color="blue")
                ax.set_xlabel("SW-PC")
                ax.set_ylabel("Depth")
                ax.invert_yaxis()  
                ax.grid(True)
                ax.legend()

                st.pyplot(fig)  

                st.success("Well log plotted successfully!")

                
                st.subheader("Comprehensive Well Log Visualization")

                try:
                    initial_features = ["Cali", "CGR", "DTCO", "NPHI", "PEF", "PHIE", "RHOB", "log(RLA3)", "log(RLA5)", "SGR"]
                    available_features = [feature for feature in initial_features if feature in selected_data.columns]

                   
                    x_ranges = {
                        "Cali": (7, 13),
                        "CGR": (0, 100),
                        "DTCO": (40, 80),
                        "NPHI": (-0.1, 0.3),
                        "PEF": (2, 8),
                        "PHIE": (0, 1),
                        "RHOB": (1.5, 3.5),
                        "log(RLA3)": (2, 10),
                        "log(RLA5)": (2, 10),
                        "SGR": (0, 60),
                    }
                    x_labels = {
                        "Cali": "Cali (in)",
                        "CGR": "CGR (GAPI)",
                        "DTCO": "DTCO (US/F)",
                        "NPHI": "NPHI (V/V)",
                        "PEF": "PEF (API)",
                        "PHIE": "PHIE (V/V)",
                        "RHOB": "RHOB (G/CM³)",
                        "log(RLA3)": "log(RLA3) (ohm.m)",
                        "log(RLA5)": "log(RLA5) (ohm.m)",
                        "SGR": "SGR (GAPI)",
                    }
                    colors = ["b", "g", "r", "c", "m", "k", "purple", "orange", "brown", "black"]

                    
                    fig, axes = plt.subplots(nrows=1, ncols=len(available_features), figsize=(20, 12), sharey=True)

                    for i, feature in enumerate(available_features):
                        ax = axes[i] if len(available_features) > 1 else axes
                        ax.plot(selected_data[feature], selected_data["Depth"], color=colors[i % len(colors)])
                        ax.set_xlim(x_ranges[feature])
                        ax.set_xlabel(x_labels[feature], fontsize=10)
                        ax.xaxis.set_label_position("top")
                        ax.tick_params(axis="both", which="major", labelsize=8)
                        ax.set_ylim(max(selected_data["Depth"]), min(selected_data["Depth"]))  
                        ax.grid(True)
                        ax.set_title(feature, fontsize=12)

                    axes[0].set_ylabel("Depth (m)", fontsize=10)
                    plt.tight_layout()
                    st.pyplot(fig)

                except Exception as e:
                    st.error(f"Error during comprehensive well log plotting: {e}")

            else:
                st.error("Depth column is missing in the data.")
        except Exception as e:
            st.error(f"Error during plotting: {e}")

    except Exception as e:
        st.error(f"Error processing the file: {e}")
