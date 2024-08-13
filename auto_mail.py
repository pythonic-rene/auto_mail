# prompt: create an email parser who monitors the inbox analize the data and put it in a dataframe do not hardcode email account and password, extract name email addresses, phonenumbers date of births company, company adress company phone home address chamber of comerse btw numbers from body and put it in a database


import imaplib
import email
import re
import pandas as pd
import spacy
import nltk

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nlp = spacy.load("en_core_web_sm")

def extract_info(email_body):
  doc = nlp(email_body)

  info = {
      "name": [],
      "email_addresses": [],
      "phone_numbers": [],
      "date_of_births": [],
      "company": [],
      "company_address": [],
      "company_phone": [],
      "home_address": [],
      "chamber_of_commerce": [],
      "btw_numbers": []
  }

  for entity in doc.ents:
    if entity.label_ == "PERSON":
      info["name"].append(entity.text)
    elif entity.label_ == "EMAIL":
      info["email_addresses"].append(entity.text)
    elif entity.label_ == "DATE":
      info["date_of_births"].append(entity.text)
    elif entity.label_ == "ORG":
      info["company"].append(entity.text)
    elif entity.label_ == "GPE":
      if "chamber of commerce" in entity.text.lower():
        info["chamber_of_commerce"].append(entity.text)
      else:
        info["company_address"].append(entity.text)

  # Use regex to find phone numbers and BTW numbers
  phone_pattern = r"\b(\+\d{1,2}\s?)?(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})\b"
  btw_pattern = r"BTW nummer:\s*(\w+)"

  # Extract phone numbers and flatten the list of tuples
  info["phone_numbers"] = [match for sublist in re.findall(phone_pattern, email_body) for match in sublist if match]  
  info["btw_numbers"] = re.findall(btw_pattern, email_body)
  return info

def connect_to_mailbox():
  # Get email credentials from user input (consider using environment variables for security)
  email_address = input("Enter your email address: ")
  password = input("Enter your password: ")

  # Connect to the IMAP server
  imap_server = "imap.gmail.com"  # Replace with your email provider's IMAP server
  imap = imaplib.IMAP4_SSL(imap_server)
  imap.login(email_address, password)
  return imap

def fetch_emails(imap):
  imap.select("inbox")
  status, messages = imap.search(None, "ALL")
  email_ids = messages[0].split()
  return email_ids

def process_emails(email_ids, imap):
  all_info = []

  for email_id in email_ids:
    _, msg = imap.fetch(email_id, "(RFC822)")
    raw_email = msg[0][1]
    email_message = email.message_from_bytes(raw_email)
    body = ""
    if email_message.is_multipart():
      for part in email_message.walk():
        if part.get_content_type() == "text/plain":
          body = part.get_payload(decode=True).decode("utf-8")
          break
    else:
      body = email_message.get_payload(decode=True).decode("utf-8")

    extracted_info = extract_info(body)
    all_info.append(extracted_info)

  return all_info

def create_dataframe(all_info):
  df = pd.DataFrame(all_info)
  # Flatten lists in the dataframe
  for column in df.columns:
    df[column] = df[column].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
  return df

# Main execution flow
imap = connect_to_mailbox()
email_ids = fetch_emails(imap)
all_info = process_emails(email_ids, imap)
df = create_dataframe(all_info)
print(df)

# Save to database (replace with your database connection details)
# import sqlite3
# conn = sqlite3.connect('email_data.db')
# df.to_sql('emails', conn, if_exists='replace', index=False)
# conn.close()

imap.close()
imap.logout()
