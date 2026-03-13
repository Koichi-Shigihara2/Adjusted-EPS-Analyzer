from edgar import Company, set_identity

def fetch_filings(ticker):
    # SECのルールに従い、自分の名前とメールアドレスをセットします
    # (例: "YourName yourname@example.com")
    set_identity("jamablue01@gmail.com") 
    
    company = Company(ticker)
    filings = company.get_filings(form=["10-Q","10-K"])
    return [str(filing.accession_no) for filing in filings[:8]]
