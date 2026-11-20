import io
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI()

model = joblib.load("house_model.joblib")
features = joblib.load("house_features.joblib")

#input schema
class HouseFeatures(BaseModel):
    MedInc : float = Field(gt=0, description="Median income of Neighbourhood")
    HouseAge : float = Field(gt=0, description="Average age of house in the block")
    AveRooms : float = Field(gt=0, description="Average number of rooms")
    AveBedrms : float = Field(gt=0, description="Average number of bedrooms")
    Population : float = Field(gt=0, description="Population")
    AveOccup : float = Field(gt=0, description="Average number of occupants")
    Latitude : float = Field(gt=-90, lt=90, description="Latitude")
    Longitude : float = Field(gt=-180, lt=180, description="Longitude")

#home
@app.get("/")
def home():
    return {
        "message": "California house prediction api",
        "status": "running",
        "endpoint": "Sent post request to /predict"
    }


@app.get("/health")
def health():
    return {
        "status": "running",
        "model": "Random Forest Regressor",
        "features": features,
        "avg_error": "$25,602"
    }

#prediction
@app.post("/predict")
def predict(house: HouseFeatures):
    try:
        input_data = pd.DataFrame([{
            "MedInc": house.MedInc,
            "HouseAge": house.HouseAge,
            "AveRooms": house.AveRooms,
            "AveBedrms": house.AveBedrms,
            "Population": house.Population,
            "AveOccup": house.AveOccup,
            "Latitude": house.Latitude,
            "Longitude": house.Longitude
        }])

        predicted = model.predict(input_data) [0]
        price_usd = predicted * 100000

        return {
            "predicted_price": f"$ {price_usd:,.0f}",
            "predicted_price_short": f"$ {predicted:,.2f} hundred thousands",
            "fidence_range": f"${price_usd - 25602:,.0f} to ${price_usd + 25602:,.0f}"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction failed: {str(e)}"
        )

@app.post("/predict-file")
async def predict_file(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV file is allowed")
    try:
        contents = await file.read()
        df = pd.DataFrame(io.BytesIO(contents))

        required_columns = [
            "MedInc",
            "HouseAge",
            "AveRooms",
            "AveBedrms",
            "Population",
            "AveOccup",
            "Latitude",
            "Longitude"
        ]

        missing_clumns = [
            col for col in required_columns 
            if col not in df.columns
        ]

        if missing_clumns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing columns: {', '.join(missing_clumns)}"
            )

        if len(df) == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty file"
            )

        predictions = model.predict(df[required_columns])

        df["predicted_columns_usd"] = df["predicted_columns_usd"].apply(lambda x: f"${x:,.0f}")

        output = df.to_csv(index=False)

        return StreamingResponse(
            io.StringIO(output),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; "
                "filename=predictions.csv"
            }
        )

        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Prediction failed: {str(e)}"
        )