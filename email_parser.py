import requests

API_KEY = 'api_key'
BASE_URL = 'https://api.rocketreach.co/v2/api/search'

def get_contact_info(name, company):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    
    payload = {
        "name": name,
        "current_employer": company,
        "page": 1,
        "page_size": 1
    }

    response = requests.post(BASE_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('profiles'):
            profile = data['profiles'][0]
            email = profile.get('email', None)
            phone = profile.get('phone_number', None)
            return email, phone
        else:
            print(f"Контакты не найдены для {name} из {company}")
            return None, None
    else:
        print(f"Ошибка API: {response.status_code} - {response.text}")
        return None, None


if _name_ == "_main_":
    ceo_name = "Satya Nadella"
    company_name = "Microsoft"
    email, phone = get_contact_info(ceo_name, company_name)
    print(f"Email: {email}")
    print(f"Phone: {phone}")