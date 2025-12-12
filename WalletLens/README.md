# WalletLens

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   Copy `.env.template` to `.env` and fill in your values.
   **Important**: For `GOOGLE_CLOUD_PROJECT`, use just the ID (e.g., `837577941206`), **not** `projects/837577941206`.
   - `GEMINI_API_KEY`: Your Gemini API key
   - `GOOGLE_CLOUD_PROJECT`: Your Google Cloud Project ID (number or string)

3. **Install Google Cloud SDK**:
   If you don't have the `gcloud` CLI installed, install it via Homebrew:
   ```bash
   brew install --cask google-cloud-sdk
   ```

4. **Configure Google Cloud & Enable API**:
   Run these commands to set up your project and enable BigQuery.
   Replace `YOUR_PROJECT_ID` with the same ID you put in `.env`:
   ```bash
   # 1. Login to Google Cloud
   gcloud auth login

   # 2. Set the project context
   gcloud config set project YOUR_PROJECT_ID

   # 3. Enable BigQuery API
   gcloud services enable bigquery.googleapis.com
   ```

5. **Authentication (ADC)**:
   This application requires Application Default Credentials to query BigQuery.
   **Crucial Step**: Run this command to authorize the local application:
   ```bash
   gcloud auth application-default login
   ```
   Follow the browser prompts to log in.

6. **Run the Application**:
   ```bash
   streamlit run src/main.py
   ```
