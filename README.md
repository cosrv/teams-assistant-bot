# teams-assistant-bot

teams-assistant-bot/
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── src/
│   ├── bot.py
│   ├── config.py
│   ├── assistant_manager.py
│   └── teams_handler.py
├── scripts/
│   ├── deploy.sh
│   └── health_check.sh
└── docs/
    ├── setup.md
    └── update_strategy.md



# chmod +x scrtips/deploy.sh
# ./scripts/deploy.sh


zip -r ../teams-hr-assistant.zip manifest.json color.png outline.png -x "*.DS_Store" -x "__MACOSX/*"

docker-compose up -d


docker-compose down -v