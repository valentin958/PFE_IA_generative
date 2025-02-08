import requests
from bs4 import BeautifulSoup

def analyze_page_reduc(url_to_analyze, counter, region_billet):
    try:
        response = requests.get(url_to_analyze)
        document = BeautifulSoup(response.content, 'html.parser')
        
        events = document.select('.bgbeige')
        for event in events:
            head = event.select_one('.head')
            if head:
                artist_name = head.text.split(" dans ")[0].strip()
                show_name = head.text.split(" dans ")[1].strip() if " dans " in head.text else ""
                #artist_page_url = head.find('a')['href']
                artist_page_url = head.get('href')
                show_type = event.select_one('.small').text.split("Spectacles »")[-1].strip()
                description = event.select_one('.libellepreliste').text.strip()
                location_info = event.select_one('.lieu').text.strip()
                dates = event.select_one('.sb').text.strip()
                
                # Further processing (e.g., splitting the location info into parts) goes here
                # Example: location_name, city, postal_code = process_location_info(location_info)
                
                # Extracting additional page info and photo URL
                #description_page, photo_url = analyze_page_reduc_artist(artist_page_url)
                artist_page_url="https://www.billetreduc.com/"+artist_page_url
                print("headlocal",head,"urlocal",artist_page_url)
                '''
                print(f"Artist: {artist_name}, Show: {show_name}, Type: {show_type}")
                print(f"Description: {description}, Dates: {dates}")
                print(f"Location: {location_info}")
                '''
                #print(f"More info: {description_page}, Photo URL: {photo_url}\n")
                
                # Database insertion placeholder
                # insert_into_database(artist_name, show_name, show_type, description, location_info, dates, region_billet, description_page, photo_url)

        # Handling pagination to fetch more events
        # Example: analyze_pagination(document, counter, region_billet)

    except requests.RequestException as e:
        print(f"Request failed: {e}")

def analyze_page_reduc_artist(artist_url):
    try:
        response = requests.get(artist_url)
        document = BeautifulSoup(response.content, 'html.parser')
        
        photo_url = document.select_one('.evtHeader img')['src']
        desc_chapo = document.select_one('[itemprop="description"]').text if document.select_one('[itemprop="description"]') else ""
        desc_resume = document.select_one('#speDescription').text if document.select_one('#speDescription') else ""
        critiques = document.select_one('.FicheBlocCritiques').text if document.select_one('.FicheBlocCritiques') else ""
        
        complete_description = f"{desc_chapo} {desc_resume} {critiques}"
        
        return complete_description, photo_url

    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return "", ""

if __name__ == "__main__":
    url_analyzer ="https://www.billetreduc.com/search.htm?jj=&dt=&heure=&prix=0&ages=&salle=&cp=&nbsalle=0&titre=&artistes=&tri=date&type=3&idrub=156&type=3&submit.x=101&submit.y=12" 
    #"https://www.billetreduc.com/search.htm?idrub=3&nbsalle=0&prix=0&tri=date&type=3%2C3&region=J"
    region = "Ile-de-France"  # Example region, you might want to determine this dynamically based on the URL
    analyze_page_reduc(url_analyzer, 0, region)
    '''
    # tout sur un artiste 
    artist_page_url="https://www.billetreduc.com/325461/evt.htm"
    description_page, photo_url = analyze_page_reduc_artist(artist_page_url)
    print(f"More info: {description_page}, Photo URL: {photo_url}\n")
    '''