import os
import requests

# Lê o token do GitHub injetado automaticamente pelo GitHub Actions 
GITHUB_TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
USERNAME = "joeycarvalho"  

def fetch_github_languages():
    # Query GraphQL para buscar os repositórios públicos e as linguagens de cada um
    query = """
    query($username: String!) {
      user(login: $username) {
        repositories(first: 50, ownerAffiliations: [OWNER], privacy: PUBLIC) {
          nodes {
            name
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers
    )
    
    if response.status_code != 200:
        raise Exception(f"Erro na API do GitHub: {response.status_code} - {response.text}")
        
    data = response.json()
    
    # Processa e soma o tamanho (bytes) de cada linguagem em todos os repositórios
    language_stats = {}
    repos = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    
    for repo in repos:
        langs = repo.get("languages", {}).get("edges", [])
        for lang in langs:
            name = lang["node"]["name"]
            size = lang["size"]
            language_stats[name] = language_stats.get(name, 0) + size
            
    # Calcula a porcentagem total
    total_size = sum(language_stats.values())
    if total_size == 0:
        return {}
        
    sorted_langs = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
    
    percentages = {}
    for name, size in sorted_langs[:10]: # Pega as top 10 linguagens
        percentages[name] = (size / total_size) * 100
        
    return percentages

def update_readme():
    try:
        langs = fetch_github_languages()
    except Exception as e:
        print(f"Erro ao buscar linguagens: {e}")
        return

    # Monta o conteúdo formatado
    content = "### 📊 Minhas Linguagens Mais Utilizadas (Dinâmico)\n\n"
    if langs:
        for lang, percentage in langs.items():
            content += f"- **{lang}**: {percentage:.1f}%\n"
    else:
        content += "_Nenhum dado encontrado no momento._\n"
        
    content += f"\n*Atualizado automaticamente via script Python e GitHub Actions.*"

    # Lê o README atual
    if not os.path.exists("README.md"):
        print("Arquivo README.md não encontrado.")
        return
        
    with open("README.md", "r", encoding="utf-8") as file:
        readme = file.read()

    start_tag = "<!--START_SECTION:langs-->"
    end_tag = "<!--END_SECTION:langs-->"

    if start_tag in readme and end_tag in readme:
        start_idx = readme.find(start_tag) + len(start_tag)
        end_idx = readme.find(end_tag)
        
        new_readme = readme[:start_idx] + "\n" + content + "\n" + readme[end_idx:]
        
        with open("README.md", "w", encoding="utf-8") as file:
            file.write(new_readme)
        print("README atualizado com sucesso com dados da API do GitHub!")

if __name__ == "__main__":
    update_readme()