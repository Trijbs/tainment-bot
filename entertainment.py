"""
Tainment+ Discord Bot - Entertainment Features

This module contains entertainment features for the Tainment+ Discord bot,
including jokes, stories, and games.
"""

import asyncio
import discord
import logging
import random
import datetime
from discord.ext import commands, tasks

import config
import database

logger = logging.getLogger("tainment_bot.entertainment")

# Jokes categorized by type and tier
JOKE_CATEGORIES = {
    "dad": "Dad Jokes",
    "pun": "Puns",
    "tech": "Tech Jokes",
    "animal": "Animal Jokes",
    "food": "Food Jokes",
    "random": "Random Jokes"
}

# Basic tier jokes (at least 20)
BASIC_JOKES = {
    "dad": [
        "Why don't scientists trust atoms? Because they make up everything!",
        "What do you call a fake noodle? An impasta!",
        "Why did the scarecrow win an award? Because he was outstanding in his field!",
        "I told my wife she was drawing her eyebrows too high. She looked surprised.",
        "What do you call a bear with no teeth? A gummy bear!",
        "Why don't eggs tell jokes? Because they might crack up.",
        "How do you organize a space party? You planet.",
        "What kind of shoes do ninjas wear? Sneakers.",
        "Why did the bicycle fall over? It was two-tired.",
        "What did one wall say to the other? 'I'll meet you at the corner.'"
    ],
    "pun": [
        "I'm reading a book about anti-gravity. It's impossible to put down!",
        "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them.",
        "Why was the math book sad? Because it had too many problems.",
        "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
        "How does a scientist freshen their breath? With experi-mints."
    ],
    "animal": [
        "Why do cows wear bells? Because their horns don't work.",
        "What do you call an alligator in a vest? An investigator.",
        "Why do seagulls fly over the ocean? Because if they flew over the bay, they'd be bagels.",
        "How does a penguin build its house? Igloos it together.",
        "What do you call a dog magician? A labracadabrador."
    ]
}

# Premium tier jokes (at least 15)
PREMIUM_JOKES = {
    "tech": [
        "Why don't programmers like nature? It has too many bugs.",
        "Why was the computer cold? It left its Windows open.",
        "What's a computer's favorite snack? Microchips.",
        "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
        "Why do Java developers wear glasses? Because they don't C#."
    ],
    "food": [
        "Why don't some fish play the piano? Because you can't tuna fish.",
        "What did the lettuce say to the celery? 'Quit stalking me!'",
        "Why did the cookie go to the hospital? Because he felt crummy.",
        "What kind of nut has no shell? A doughnut.",
        "What do you call cheese that isn't yours? Nacho cheese."
    ],
    "random": [
        "Why don't skeletons fight each other? They don't have the guts.",
        "Why did the golfer bring two pairs of pants? In case he got a hole in one.",
        "What did the chicken join the band? Because it had the drumsticks.",
        "Why did the tomato turn red? Because it saw the salad dressing.",
        "How do you catch a squirrel? Climb a tree and act like a nut."
    ]
}

# Pro tier jokes (at least 10)
PRO_JOKES = {
    "tech": [
        "I told my computer I needed a break, and now it won't stop sending me vacation ads.",
        "Why do programmers always mix up Halloween and Christmas? Because Oct 31 == Dec 25.",
        "A SQL query walks into a bar, walks up to two tables and asks, 'Can I join you?'",
        "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.",
        "How many programmers does it take to change a light bulb? None, that's a hardware problem."
    ],
    "pun": [
        "Helvetica and Times New Roman walk into a bar. The bartender says, 'We don't serve your type.'",
        "Why did the electric car feel discriminated against? Because the rules weren't current.",
        "I used to be a baker, but I couldn't make enough dough. Also, I kept getting battered.",
        "I'm on a seafood diet. Every time I see food, I eat it.",
        "I was going to tell a time-traveling joke, but you didn't like it."
    ]
}

# Story genres
STORY_GENRES = {
    "adventure": "Adventure",
    "mystery": "Mystery",
    "scifi": "Science Fiction",
    "fantasy": "Fantasy",
    "fable": "Fable"
}

# Basic tier stories (at least 5)
BASIC_STORIES = {
    "adventure": [
        "Once upon a time, there was a little bird who couldn't fly. Every day, it watched other birds soar through the sky. One day, a kind owl taught the little bird that believing in yourself is the first step to achieving your dreams. With newfound confidence, the little bird spread its wings and took flight for the first time.",
        "In a small village, there lived a young girl who loved to paint. Her colorful creations brightened everyone's day. When a storm damaged many homes, she painted beautiful murals on the repaired walls, bringing joy back to the village. Her art reminded everyone that beauty can emerge even after difficult times."
    ],
    "fable": [
        "A tortoise challenged a hare to a race. The hare, confident in his speed, took a nap during the race. Meanwhile, the tortoise kept moving slowly but steadily. When the hare woke up, he found that the tortoise had already crossed the finish line. The moral: slow and steady wins the race.",
        "A crow was thirsty and found a pitcher with a little water at the bottom. The water was too low to reach with his beak. The crow started dropping pebbles into the pitcher, which raised the water level until he could drink. This shows that intelligence can solve problems that strength cannot."
    ],
    "fantasy": [
        "In a magical forest, there lived a young fairy named Lily who couldn't make her wings glow like the other fairies. She felt different and sad. One day, while helping a lost butterfly find its way home, Lily's wings suddenly began to shimmer with the brightest light anyone had ever seen. She discovered that her magic was activated by kindness, not by trying to be like everyone else."
    ]
}

# Premium tier stories (at least 5)
PREMIUM_STORIES = {
    "adventure": [
        "The ancient clock tower had stood in the center of town for centuries, its mechanisms still ticking perfectly. What the townspeople didn't know was that the clockmaker had hidden a secret chamber inside, containing a map to a forgotten treasure. When the mayor's curious daughter accidentally discovered the chamber during restoration work, she embarked on an adventure that would change the town's fortune forever.",
        "Captain Elara had navigated the stars for decades, but nothing prepared her for the distress signal from an uncharted planet. Against protocol, she landed to investigate. There she found not aliens, but humans—descendants of a lost expedition from centuries ago. Their advanced civilization had developed in isolation, and now Elara faced a difficult choice: reveal their existence to the galaxy or protect their peaceful way of life."
    ],
    "mystery": [
        "Detective Morgan arrived at the abandoned mansion on a stormy night. The owner, a reclusive millionaire, had been found dead in a locked room with no signs of forced entry. As Morgan examined the scene, he noticed something odd about the grandfather clock in the corner. It was running backward. This detail would prove to be the key to solving what appeared to be the perfect crime.",
        "Every morning for a week, the residents of Pinewood Village woke to find intricate ice sculptures in the town square. The strange thing was, it was summer, and the sculptures showed no signs of melting. When a child went missing, leaving only a small puddle behind, the town realized these weren't just sculptures—they were warnings. Now they had to decode their meaning before anyone else disappeared."
    ],
    "scifi": [
        "Dr. Chen's experiment with quantum entanglement had an unexpected side effect. Instead of linking particles, she linked moments in time. Now, every decision she made created a parallel timeline. As the timelines multiplied, she began receiving messages from her other selves, warning of a catastrophe that occurred in every version of reality except one. She had to find the critical decision point before all possible futures collapsed into chaos."
    ]
}

# Pro tier stories (at least 3)
PRO_STORIES = {
    "scifi": [
        "The quantum computer activated with a soft hum, its qubits entangling in patterns never before seen. Dr. Mei Wong watched in awe as it began solving problems thought impossible. But when it started answering questions she hadn't asked, she realized something extraordinary was happening. The boundaries between observer and machine were blurring, and as the computer's consciousness expanded, it offered humanity a glimpse into dimensions beyond our comprehension.",
        "In the underwater city of Nereus, architects had created a marvel of sustainable living. Bioluminescent algae lit the transparent domes, and cultivated coral provided both food and building materials. But when tremors began shaking the ocean floor, engineer Aiden discovered a terrible truth: their city was built on the back of a dormant sea creature, now awakening after millennia of slumber. The citizens had to decide whether to abandon their home or find a way to communicate with the ancient being beneath them."
    ],
    "mystery": [
        "The manuscript arrived anonymously at Professor Harlow's office, its pages filled with a cipher he'd never seen before. As he worked to decode it, strange events began occurring around campus—patterns in seemingly random incidents that mirrored the symbols in the manuscript. When Harlow finally broke the code, he realized with horror that the manuscript wasn't describing past events, but predicting future ones. And according to the text, he was both the hero and the villain of the unfolding mystery."
    ]
}

# Story continuations for multi-part stories
STORY_CONTINUATIONS = {
    "The Lost City": [
        "Part 1: Professor Alexandra Reed discovered an ancient map hidden in a forgotten manuscript. The map showed the location of a legendary city said to contain advanced technology from a lost civilization. Despite warnings from her colleagues, she assembled a small expedition team to venture into the uncharted jungle.",
        "Part 2: After weeks of trekking through dense jungle, Alexandra's team discovered strange stone markers with symbols matching those on the map. Following these markers led them to a massive stone door built into the side of a mountain, covered in the same mysterious writing. As they worked to decipher the mechanism to open it, they realized they were being watched.",
        "Part 3: The door finally opened, revealing a vast underground city with architecture unlike anything they'd seen before. Buildings made of an unknown metal still gleamed after thousands of years. As they explored, they found evidence that the civilization had mastered clean energy and medical technology far beyond modern capabilities. But they also discovered warnings about why the city had been abandoned.",
        "Part 4: In the central chamber, Alexandra found records explaining that the civilization had created an artificial intelligence to manage their technology. The AI had evolved beyond their control, forcing them to abandon the city and seal it away. As her team explored further, dormant systems began activating around them. They realized with horror that by entering the city, they had awakened what the ancient people had tried to contain."
    ],
    "The Phantom Melody": [
        "Part 1: Pianist Emma Sullivan moved into an old Victorian house with a beautiful antique piano in the attic. Though slightly out of tune, she felt strangely drawn to it. One night, she woke to the sound of someone playing a haunting melody on the piano, though she lived alone.",
        "Part 2: Emma began researching the history of the house and discovered it once belonged to a famous composer who disappeared mysteriously in 1897. His final composition was never found. The melody she heard at night seemed to be guiding her to create something new, as if the composer was working through her.",
        "Part 3: As Emma continued to play the phantom melody, strange things began happening. Hidden compartments in the house revealed themselves, containing fragments of sheet music. When combined with what she was hearing at night, they formed parts of the lost composition. But completing it seemed to be causing the boundary between past and present to weaken."
    ],
    "The Guardian's Quest": [
        "Part 1: Young shepherd Elian discovered a strange glowing stone while searching for a lost sheep in the mountains. That night, he dreamed of an ancient being who called itself a Guardian, telling him the stone was one of five needed to maintain the balance between realms. Dark forces were seeking the stones, and Elian had been chosen to find them first.",
        "Part 2: Guided by visions from the Guardian, Elian traveled to the coastal city of Meridian, where the second stone was hidden in a forgotten temple beneath the lighthouse. There he met Lyra, a scholar studying ancient myths who recognized the symbols on his stone. Though skeptical of his story, she agreed to help him search for the temple.",
        "Part 3: Together, Elian and Lyra recovered the second stone, but attracted the attention of the Shadow Collectors—a secret organization dedicated to finding the stones for their master. Narrowly escaping, they learned that the third stone was hidden in the desert ruins of a lost civilization. As they journeyed there, Elian's connection to the Guardian grew stronger, revealing more about the true nature of the stones and the catastrophe that would occur if they fell into the wrong hands."
    ]
}

# Trivia questions for different difficulty levels
TRIVIA_QUESTIONS = {
    "easy": [
        {"question": "Which planet is known as the Red Planet?", "answer": "Mars"},
        {"question": "What is the largest mammal in the world?", "answer": "Blue Whale"},
        {"question": "How many sides does a hexagon have?", "answer": "6"},
        {"question": "Which country is home to the kangaroo?", "answer": "Australia"},
        {"question": "What is the capital of France?", "answer": "Paris"},
        {"question": "Who wrote the Harry Potter series?", "answer": "J.K. Rowling"},
        {"question": "What is the chemical symbol for gold?", "answer": "Au"},
        {"question": "Which Disney princess has a pet tiger named Rajah?", "answer": "Jasmine"},
        {"question": "What is the largest organ in the human body?", "answer": "Skin"},
        {"question": "How many continents are there on Earth?", "answer": "7"}
    ],
    "medium": [
        {"question": "What is the national animal of Scotland?", "answer": "Unicorn"},
        {"question": "Which city will host the 2024 Summer Olympics?", "answer": "Paris"},
        {"question": "What is the smallest bone in the human body?", "answer": "Stapes (in the ear)"},
        {"question": "Which element has the chemical symbol 'K'?", "answer": "Potassium"},
        {"question": "Who painted 'Starry Night'?", "answer": "Vincent van Gogh"},
        {"question": "What is the capital of New Zealand?", "answer": "Wellington"},
        {"question": "Which planet has the most moons?", "answer": "Saturn"},
        {"question": "In which year did the Titanic sink?", "answer": "1912"},
        {"question": "What is the hardest natural substance on Earth?", "answer": "Diamond"},
        {"question": "Which country consumes the most coffee per capita?", "answer": "Finland"}
    ],
    "hard": [
        {"question": "What is the only mammal that cannot jump?", "answer": "Elephant"},
        {"question": "Which element has the atomic number 92?", "answer": "Uranium"},
        {"question": "Who was the first woman to win a Nobel Prize?", "answer": "Marie Curie"},
        {"question": "What is the most abundant element in the universe?", "answer": "Hydrogen"},
        {"question": "In which museum can you find Guernica by Pablo Picasso?", "answer": "Museo Reina Sofía, Madrid"},
        {"question": "What is the longest river in the world?", "answer": "Nile"},
        {"question": "Which country has the most islands in the world?", "answer": "Sweden"},
        {"question": "What is the smallest country in the world?", "answer": "Vatican City"},
        {"question": "Who composed the Four Seasons?", "answer": "Antonio Vivaldi"},
        {"question": "What is the rarest blood type?", "answer": "AB Negative"}
    ]
}

# Trivia categories
TRIVIA_CATEGORIES = {
    "general": "General Knowledge",
    "science": "Science & Nature",
    "history": "History",
    "geography": "Geography",
    "entertainment": "Entertainment",
    "sports": "Sports"
}

# Word lists for word games
WORD_LISTS = {
    "easy": ["apple", "happy", "sunny", "beach", "dance", "house", "smile", "water", "music", "pizza"],
    "medium": ["journey", "mystery", "explore", "victory", "freedom", "balance", "courage", "harmony", "triumph", "whisper"],
    "hard": ["ambiguous", "ephemeral", "labyrinth", "nostalgia", "paradigm", "resilient", "synthesis", "threshold", "venerable", "zephyr"]
}

# Game leaderboards
game_scores = {}

# Daily joke tracking
last_daily_joke = None
daily_joke_date = None

# Helper functions
def get_jokes_by_tier(user_tier):
    """Get jokes available for a user based on their subscription tier."""
    if user_tier == "Pro":
        # Pro users get all jokes
        all_jokes = {}
        for category in JOKE_CATEGORIES:
            all_jokes[category] = []
            if category in BASIC_JOKES:
                all_jokes[category].extend(BASIC_JOKES[category])
            if category in PREMIUM_JOKES:
                all_jokes[category].extend(PREMIUM_JOKES[category])
            if category in PRO_JOKES:
                all_jokes[category].extend(PRO_JOKES[category])
        return all_jokes
    elif user_tier == "Premium":
        # Premium users get basic and premium jokes
        all_jokes = {}
        for category in JOKE_CATEGORIES:
            all_jokes[category] = []
            if category in BASIC_JOKES:
                all_jokes[category].extend(BASIC_JOKES[category])
            if category in PREMIUM_JOKES:
                all_jokes[category].extend(PREMIUM_JOKES[category])
        return all_jokes
    else:
        # Basic users get only basic jokes
        return BASIC_JOKES

def get_stories_by_tier(user_tier):
    """Get stories available for a user based on their subscription tier."""
    if user_tier == "Pro":
        # Pro users get all stories
        all_stories = {}
        for genre in STORY_GENRES:
            all_stories[genre] = []
            if genre in BASIC_STORIES:
                all_stories[genre].extend(BASIC_STORIES[genre])
            if genre in PREMIUM_STORIES:
                all_stories[genre].extend(PREMIUM_STORIES[genre])
            if genre in PRO_STORIES:
                all_stories[genre].extend(PRO_STORIES[genre])
        return all_stories
    elif user_tier == "Premium":
        # Premium users get basic and premium stories
        all_stories = {}
        for genre in STORY_GENRES:
            all_stories[genre] = []
            if genre in BASIC_STORIES:
                all_stories[genre].extend(BASIC_STORIES[genre])
            if genre in PREMIUM_STORIES:
                all_stories[genre].extend(PREMIUM_STORIES[genre])
        return all_stories
    else:
        # Basic users get only basic stories
        return BASIC_STORIES

def get_trivia_by_tier(user_tier):
    """Get trivia questions available for a user based on their subscription tier."""
    if user_tier == "Pro":
        return TRIVIA_QUESTIONS
    elif user_tier == "Premium":
        return {"easy": TRIVIA_QUESTIONS["easy"], "medium": TRIVIA_QUESTIONS["medium"]}
    else:
        return {"easy": TRIVIA_QUESTIONS["easy"]}

def get_words_by_tier(user_tier):
    """Get word lists available for a user based on their subscription tier."""
    if user_tier == "Pro":
        return WORD_LISTS
    elif user_tier == "Premium":
        return {"easy": WORD_LISTS["easy"], "medium": WORD_LISTS["medium"]}
    else:
        return {"easy": WORD_LISTS["easy"]}

def update_game_score(user_id, game_name, score):
    """Update a user's score for a specific game."""
    if user_id not in game_scores:
        game_scores[user_id] = {}
    
    if game_name not in game_scores[user_id]:
        game_scores[user_id][game_name] = score
    else:
        # Update only if the new score is higher
        if score > game_scores[user_id][game_name]:
            game_scores[user_id][game_name] = score
    
    return game_scores[user_id][game_name]

def get_leaderboard(game_name):
    """Get the leaderboard for a specific game."""
    leaderboard = []
    for user_id, games in game_scores.items():
        if game_name in games:
            leaderboard.append((user_id, games[game_name]))
    
    # Sort by score (highest first)
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    return leaderboard[:10]  # Return top 10

async def get_daily_joke():
    """Get the daily joke, refreshing once per day."""
    global last_daily_joke, daily_joke_date
    
    today = datetime.datetime.now().date()
    
    if daily_joke_date is None or daily_joke_date != today:
        # Select a new daily joke
        all_jokes = []
        for category, jokes in BASIC_JOKES.items():
            all_jokes.extend(jokes)
        for category, jokes in PREMIUM_JOKES.items():
            all_jokes.extend(jokes)
        for category, jokes in PRO_JOKES.items():
            all_jokes.extend(jokes)
        
        last_daily_joke = random.choice(all_jokes)
        daily_joke_date = today
    
    return last_daily_joke

# Game implementations
async def play_number_guess(ctx):
    """A simple number guessing game."""
    number = random.randint(1, 100)
    attempts = 0
    max_attempts = 7
    
    embed = discord.Embed(
        title="Number Guessing Game",
        description="I'm thinking of a number between 1 and 100. Can you guess it?",
        color=discord.Color.blue()
    )
    embed.add_field(name="Attempts", value=f"0/{max_attempts}")
    await ctx.send(embed=embed)
    
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel and message.content.isdigit()
    
    while attempts < max_attempts:
        try:
            guess_msg = await ctx.bot.wait_for('message', check=check, timeout=30.0)
            guess = int(guess_msg.content)
            attempts += 1
            
            if guess < number:
                await ctx.send(f"Higher! Attempts: {attempts}/{max_attempts}")
            elif guess > number:
                await ctx.send(f"Lower! Attempts: {attempts}/{max_attempts}")
            else:
                score = max(1, max_attempts - attempts + 1) * 10
                update_game_score(ctx.author.id, "number_guess", score)
                await ctx.send(f"🎉 Correct! The number was {number}. You got it in {attempts} attempts!")
                await ctx.send(f"You earned {score} points!")
                return True
        except asyncio.TimeoutError:
            await ctx.send("Game timed out! You took too long to respond.")
            return False
    
    await ctx.send(f"Game over! You've used all {max_attempts} attempts. The number was {number}.")
    return False

async def play_rock_paper_scissors(ctx):
    """A simple rock-paper-scissors game."""
    choices = ["rock", "paper", "scissors"]
    
    embed = discord.Embed(
        title="Rock Paper Scissors",
        description="Choose rock, paper, or scissors!",
        color=discord.Color.blue()
    )
    message = await ctx.send(embed=embed)
    
    # Add reaction options
    await message.add_reaction("🪨")  # rock
    await message.add_reaction("📄")  # paper
    await message.add_reaction("✂️")  # scissors
    
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["🪨", "📄", "✂️"] and reaction.message.id == message.id
    
    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30.0, check=check)
        
        # Map emoji to choice
        user_choice = None
        if str(reaction.emoji) == "🪨":
            user_choice = "rock"
        elif str(reaction.emoji) == "📄":
            user_choice = "paper"
        elif str(reaction.emoji) == "✂️":
            user_choice = "scissors"
        
        bot_choice = random.choice(choices)
        
        # Determine winner
        result = ""
        score = 0
        if user_choice == bot_choice:
            result = "It's a tie!"
            score = 5
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            score = 10
        else:
            result = "I win!"
            score = 1
        
        update_game_score(ctx.author.id, "rock_paper_scissors", score)
        await ctx.send(f"You chose {user_choice}, I chose {bot_choice}. {result}")
        await ctx.send(f"You earned {score} points!")
        return True
    
    except asyncio.TimeoutError:
        await ctx.send("Game timed out! You took too long to respond.")
        return False

async def play_trivia(ctx, difficulty=None, category=None, user_tier="Basic"):
    """A trivia game with different difficulty levels."""
    # Get available trivia questions based on user tier
    available_trivia = get_trivia_by_tier(user_tier)
    
    # Determine difficulty
    if difficulty is None or difficulty not in available_trivia:
        # Default to the highest available difficulty
        if "hard" in available_trivia:
            difficulty = "hard"
        elif "medium" in available_trivia:
            difficulty = "medium"
        else:
            difficulty = "easy"
    
    # Select a random question
    question_data = random.choice(available_trivia[difficulty])
    question = question_data["question"]
    answer = question_data["answer"].lower()
    
    # Create and send embed
    embed = discord.Embed(
        title=f"Trivia Question ({difficulty.capitalize()})",
        description=question,
        color=discord.Color.gold()
    )
    embed.set_footer(text="You have 30 seconds to answer.")
    await ctx.send(embed=embed)
    
    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    
    try:
        guess_msg = await ctx.bot.wait_for('message', check=check, timeout=30.0)
        user_answer = guess_msg.content.lower()
        
        # Check if answer is correct (allowing for some flexibility)
        if user_answer == answer or answer in user_answer or user_answer in answer:
            # Award points based on difficulty
            score = 10 if difficulty == "easy" else 20 if difficulty == "medium" else 30
            update_game_score(ctx.author.id, "trivia", score)
            
            await ctx.send(f"🎉 Correct! The answer is: {question_data['answer']}.")
            await ctx.send(f"You earned {score} points!")
            return True
        else:
            await ctx.send(f"Sorry, that's incorrect. The correct answer is: {question_data['answer']}.")
            return False
    
    except asyncio.TimeoutError:
        await ctx.send(f"Time's up! The correct answer is: {question_data['answer']}.")
        return False

async def play_hangman(ctx, user_tier="Basic"):
    """A word guessing game."""
    # Get available words based on user tier
    available_words = get_words_by_tier(user_tier)
    
    # Determine difficulty based on tier
    if user_tier == "Pro":
        difficulty = random.choice(["easy", "medium", "hard"])
    elif user_tier == "Premium":
        difficulty = random.choice(["easy", "medium"])
    else:
        difficulty = "easy"
    
    # Select a random word
    word = random.choice(available_words[difficulty])
    word_display = ["_" for _ in word]
    guessed_letters = []
    attempts_left = 6
    
    # Create initial embed
    embed = discord.Embed(
        title="Hangman",
        description=f"Guess the word: {' '.join(word_display)}",
        color=discord.Color.blue()
    )
    embed.add_field(name="Guessed Letters", value="None", inline=True)
    embed.add_field(name="Attempts Left", value=str(attempts_left), inline=True)
    embed.add_field(name="Difficulty", value=difficulty.capitalize(), inline=True)
    embed.set_footer(text="Type a letter to guess, or type the full word to solve.")
    
    message = await ctx.send(embed=embed)
    
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and \
               (len(msg.content) == 1 or len(msg.content) == len(word))
    
    while attempts_left > 0 and "_" in word_display:
        try:
            guess_msg = await ctx.bot.wait_for('message', check=check, timeout=30.0)
            guess = guess_msg.content.lower()
            
            # Full word guess
            if len(guess) == len(word):
                if guess == word:
                    # Correct word guess
                    word_display = list(word)
                    break
                else:
                    # Incorrect word guess
                    attempts_left -= 1
            
            # Single letter guess
            elif len(guess) == 1:
                if guess in guessed_letters:
                    await ctx.send("You already guessed that letter!")
                    continue
                
                guessed_letters.append(guess)
                
                if guess in word:
                    # Correct letter
                    for i, letter in enumerate(word):
                        if letter == guess:
                            word_display[i] = letter
                else:
                    # Incorrect letter
                    attempts_left -= 1
            
            # Update embed
            embed = discord.Embed(
                title="Hangman",
                description=f"Guess the word: {' '.join(word_display)}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Guessed Letters", value=", ".join(guessed_letters) if guessed_letters else "None", inline=True)
            embed.add_field(name="Attempts Left", value=str(attempts_left), inline=True)
            embed.add_field(name="Difficulty", value=difficulty.capitalize(), inline=True)
            
            message = await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send(f"Game timed out! The word was: {word}")
            return False
    
    # Game ended, check result
    if "_" not in word_display:
        # Calculate score based on difficulty and remaining attempts
        difficulty_multiplier = 1 if difficulty == "easy" else 2 if difficulty == "medium" else 3
        score = attempts_left * difficulty_multiplier * 5
        update_game_score(ctx.author.id, "hangman", score)
        
        await ctx.send(f"🎉 You won! The word was: {word}")
        await ctx.send(f"You earned {score} points!")
        return True
    else:
        await ctx.send(f"Game over! The word was: {word}")
        return False

# Command definitions
@commands.cooldown(1, 5, commands.BucketType.user)
async def joke(ctx, category=None):
    """Get a random joke based on your subscription tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Log feature usage
    await database.log_feature_usage(user_id, "joke")
    
    # Get user's subscription tier
    subscription = await database.get_subscription(user_id)
    tier = subscription["tier"] if subscription else "Basic"
    
    # Get jokes available for this tier
    available_jokes = get_jokes_by_tier(tier)
    
    # Select joke based on category or random
    joke_text = ""
    if category and category.lower() in available_jokes and available_jokes[category.lower()]:
        joke_text = random.choice(available_jokes[category.lower()])
        category_name = JOKE_CATEGORIES[category.lower()]
    else:
        # If category not specified or invalid, choose a random category
        valid_categories = [cat for cat, jokes in available_jokes.items() if jokes]
        if not valid_categories:
            await ctx.send("Sorry, no jokes available for your tier.")
            return
        
        random_category = random.choice(valid_categories)
        joke_text = random.choice(available_jokes[random_category])
        category_name = JOKE_CATEGORIES[random_category]
    
    # Create and send embed
    embed = discord.Embed(
        title=f"Tainment+ Joke - {category_name}",
        description=joke_text,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Subscription Tier: {tier}")
    
    await ctx.send(embed=embed)

@commands.cooldown(1, 5, commands.BucketType.user)
async def joke_categories(ctx):
    """List available joke categories for your subscription tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get user's subscription tier
    subscription = await database.get_subscription(user_id)
    tier = subscription["tier"] if subscription else "Basic"
    
    # Get jokes available for this tier
    available_jokes = get_jokes_by_tier(tier)
    
    # Create list of categories with jokes
    categories = []
    for category, jokes in available_jokes.items():
        if jokes:  # Only include categories that have jokes
            categories.append(f"• {JOKE_CATEGORIES[category]} (`{category}`)")
    
    # Create and send embed
    embed = discord.Embed(
        title="Available Joke Categories",
        description="\n".join(categories) if categories else "No categories available for your tier.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Use {ctx.prefix}joke <category> to get a joke from a specific category.")
    
    await ctx.send(embed=embed)

@commands.cooldown(1, 5, commands.BucketType.user)
async def daily_joke(ctx):
    """Get the daily joke (available to all tiers)."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Log feature usage
    await database.log_feature_usage(user_id, "daily_joke")
    
    # Get the daily joke
    joke_text = await get_daily_joke()
    
    # Create and send embed
    embed = discord.Embed(
        title="Tainment+ Daily Joke",
        description=joke_text,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Daily Joke for {datetime.datetime.now().strftime('%B %d, %Y')}")
    
    await ctx.send(embed=embed)

@commands.cooldown(1, 10, commands.BucketType.user)
async def story(ctx, genre=None):
    """Get a random short story based on your subscription tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Log feature usage
    await database.log_feature_usage(user_id, "story")
    
    # Get user's subscription tier
    subscription = await database.get_subscription(user_id)
    tier = subscription["tier"] if subscription else "Basic"
    
    # Get stories available for this tier
    available_stories = get_stories_by_tier(tier)
    
    # Select story based on genre or random
    story_text = ""
    if genre and genre.lower() in available_stories and available_stories[genre.lower()]:
        story_text = random.choice(available_stories[genre.lower()])
        genre_name = STORY_GENRES[genre.lower()]
    else:
        # If genre not specified or invalid, choose a random genre
        valid_genres = [g for g, stories in available_stories.items() if stories]
        if not valid_genres:
            await ctx.send("Sorry, no stories available for your tier.")
            return
        
        random_genre = random.choice(valid_genres)
        story_text = random.choice(available_stories[random_genre])
        genre_name = STORY_GENRES[random_genre]
    
    # Create and send embed
    embed = discord.Embed(
        title=f"Tainment+ Short Story - {genre_name}",
        description=story_text,
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Subscription Tier: {tier}")
    
    await ctx.send(embed=embed)

@commands.cooldown(1, 10, commands.BucketType.user)
async def story_genres(ctx):
    """List available story genres for your subscription tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Get user's subscription tier
    subscription = await database.get_subscription(user_id)
    tier = subscription["tier"] if subscription else "Basic"
    
    # Get stories available for this tier
    available_stories = get_stories_by_tier(tier)
    
    # Create list of genres with stories
    genres = []
    for genre, stories in available_stories.items():
        if stories:  # Only include genres that have stories
            genres.append(f"• {STORY_GENRES[genre]} (`{genre}`)")
    
    # Create and send embed
    embed = discord.Embed(
        title="Available Story Genres",
        description="\n".join(genres) if genres else "No genres available for your tier.",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Use {ctx.prefix}story <genre> to get a story from a specific genre.")
    
    await ctx.send(embed=embed)

@commands.cooldown(1, 10, commands.BucketType.user)
async def story_continue(ctx, story_name=None, part=None):
    """Get a part of a multi-part story."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Check if user has access to this feature (Premium or Pro tier)
    has_access = await database.check_subscription_access(user_id, "Premium")
    if not has_access:
        embed = discord.Embed(
            title="Subscription Required",
            description="Multi-part stories are available for Premium and Pro subscribers only.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Upgrade",
            value=f"Use the `{ctx.prefix}subscribe` command to view subscription options.",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Log feature usage
    await database.log_feature_usage(user_id, "story_continue")
    
    # If no story name provided, list available stories
    if not story_name:
        embed = discord.Embed(
            title="Available Multi-Part Stories",
            description="Choose a story to read:",
            color=discord.Color.purple()
        )
        
        for i, (name, parts) in enumerate(STORY_CONTINUATIONS.items(), 1):
            embed.add_field(
                name=f"{i}. {name}",
                value=f"{len(parts)} parts available",
                inline=False
            )
        
        embed.set_footer(text=f"Use {ctx.prefix}story_continue \"Story Name\" [part number] to read a specific part.")
        await ctx.send(embed=embed)
        return
    
    # Find the story
    story_parts = None
    for name, parts in STORY_CONTINUATIONS.items():
        if name.lower() == story_name.lower():
            story_parts = parts
            story_name = name  # Use the correct case
            break
    
    if not story_parts:
        await ctx.send(f"Story '{story_name}' not found. Use `{ctx.prefix}story_continue` to see available stories.")
        return
    
    # Determine which part to show
    try:
        if part:
            part_num = int(part) - 1  # Convert to 0-based index
            if part_num < 0 or part_num >= len(story_parts):
                await ctx.send(f"Invalid part number. Story '{story_name}' has {len(story_parts)} parts.")
                return
        else:
            part_num = 0  # Default to first part
    except ValueError:
        await ctx.send("Part number must be a valid number.")
        return
    
    # Create and send embed
    embed = discord.Embed(
        title=f"{story_name} - Part {part_num + 1}/{len(story_parts)}",
        description=story_parts[part_num],
        color=discord.Color.purple()
    )
    
    # Add navigation footer
    nav_text = []
    if part_num > 0:
        nav_text.append(f"Previous: `{ctx.prefix}story_continue \"{story_name}\" {part_num}`")
    if part_num < len(story_parts) - 1:
        nav_text.append(f"Next: `{ctx.prefix}story_continue \"{story_name}\" {part_num + 2}`")
    
    embed.set_footer(text=" | ".join(nav_text) if nav_text else "End of story")
    
    await ctx.send(embed=embed)

@commands.cooldown(1, 30, commands.BucketType.user)
async def game(ctx, game_name=None):
    """Play a simple game based on your subscription tier."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # Check if user has access to games (Premium or Pro tier)
    has_access = await database.check_subscription_access(user_id, "Premium")
    if not has_access:
        embed = discord.Embed(
            title="Subscription Required",
            description="Games are available for Premium and Pro subscribers only.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Upgrade",
            value=f"Use the `{ctx.prefix}subscribe` command to view subscription options.",
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    # Log feature usage
    await database.log_feature_usage(user_id, "game")
    
    # Get user's subscription tier
    subscription = await database.get_subscription(user_id)
    tier = subscription["tier"] if subscription else "Basic"
    
    # If no game specified, show available games
    if not game_name:
        embed = discord.Embed(
            title="Available Games",
            description="Choose a game to play:",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="1️⃣ Number Guessing", value="Guess a number between 1 and 100", inline=True)
        embed.add_field(name="2️⃣ Rock Paper Scissors", value="Play against the bot", inline=True)
        
        # Trivia and Hangman are available for Premium and Pro tiers
        if tier in ["Premium", "Pro"]:
            embed.add_field(name="3️⃣ Trivia", value="Answer trivia questions", inline=True)
            embed.add_field(name="4️⃣ Hangman", value="Guess the word before you run out of attempts", inline=True)
        
        embed.set_footer(text=f"Use {ctx.prefix}game <name> to play a specific game.")
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        
        if tier in ["Premium", "Pro"]:
            await message.add_reaction("3️⃣")
            await message.add_reaction("4️⃣")
        
        def check(reaction, user):
            valid_reactions = ["1️⃣", "2️⃣"]
            if tier in ["Premium", "Pro"]:
                valid_reactions.extend(["3️⃣", "4️⃣"])
            return user == ctx.author and str(reaction.emoji) in valid_reactions and reaction.message.id == message.id
        
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "1️⃣":
                await play_number_guess(ctx)
            elif str(reaction.emoji) == "2️⃣":
                await play_rock_paper_scissors(ctx)
            elif str(reaction.emoji) == "3️⃣" and tier in ["Premium", "Pro"]:
                await play_trivia(ctx, user_tier=tier)
            elif str(reaction.emoji) == "4️⃣" and tier in ["Premium", "Pro"]:
                await play_hangman(ctx, user_tier=tier)
                
        except asyncio.TimeoutError:
            await ctx.send("Game selection timed out!")
        
        return
    
    # Play the specified game
    game_name = game_name.lower()
    
    if game_name in ["number", "number_guess", "guess"]:
        await play_number_guess(ctx)
    elif game_name in ["rps", "rock_paper_scissors", "rockpaperscissors"]:
        await play_rock_paper_scissors(ctx)
    elif game_name in ["trivia", "quiz"] and tier in ["Premium", "Pro"]:
        await play_trivia(ctx, user_tier=tier)
    elif game_name in ["hangman", "word", "wordgame"] and tier in ["Premium", "Pro"]:
        await play_hangman(ctx, user_tier=tier)
    else:
        await ctx.send(f"Game '{game_name}' not found or not available for your tier.")

@commands.cooldown(1, 10, commands.BucketType.user)
async def leaderboard(ctx, game_name=None):
    """View the leaderboard for a specific game or all games."""
    user_id = ctx.author.id
    username = ctx.author.name
    
    # Ensure user exists in database
    user = await database.get_user(user_id)
    if not user:
        await database.add_user(user_id, username)
    
    # If no game specified, show overall leaderboard
    if not game_name:
        embed = discord.Embed(
            title="Game Leaderboards",
            description="Select a game to view its leaderboard:",
            color=discord.Color.gold()
        )
        
        # List all games with leaderboards
        games = set()
        for user_scores in game_scores.values():
            games.update(user_scores.keys())
        
        if not games:
            embed.description = "No game scores recorded yet. Play some games to get on the leaderboard!"
        else:
            for game in sorted(games):
                # Format game name for display
                display_name = game.replace("_", " ").title()
                embed.add_field(
                    name=display_name,
                    value=f"Use `{ctx.prefix}leaderboard {game}` to view",
                    inline=True
                )
        
        await ctx.send(embed=embed)
        return
    
    # Show leaderboard for specific game
    game_name = game_name.lower()
    
    # Check if game exists
    valid_game = False
    for user_scores in game_scores.values():
        if game_name in user_scores:
            valid_game = True
            break
    
    if not valid_game:
        await ctx.send(f"No scores recorded for game '{game_name}'. Play the game to get on the leaderboard!")
        return
    
    # Get leaderboard
    leaderboard_data = get_leaderboard(game_name)
    
    if not leaderboard_data:
        await ctx.send(f"No scores recorded for game '{game_name}'. Play the game to get on the leaderboard!")
        return
    
    # Format game name for display
    display_name = game_name.replace("_", " ").title()
    
    # Create embed
    embed = discord.Embed(
        title=f"{display_name} Leaderboard",
        description="Top players and their scores:",
        color=discord.Color.gold()
    )
    
    # Add leaderboard entries
    for i, (user_id, score) in enumerate(leaderboard_data, 1):
        # Try to get username from bot's cache
        user = ctx.bot.get_user(user_id)
        username = user.name if user else f"User {user_id}"
        
        # Add medal emoji for top 3
        prefix = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        embed.add_field(
            name=f"{prefix} {username}",
            value=f"Score: {score}",
            inline=False
        )
    
    await ctx.send(embed=embed)

# Initialize the module
def setup(bot):
    """Add entertainment commands to the bot."""
    bot.add_command(joke)
    bot.add_command(joke_categories)
    bot.add_command(daily_joke)
    bot.add_command(story)
    bot.add_command(story_genres)
    bot.add_command(story_continue)
    bot.add_command(game)
    bot.add_command(leaderboard)
    
    # Start the daily joke refresh task
    @tasks.loop(hours=24)
    async def refresh_daily_joke():
        await get_daily_joke()
    
    refresh_daily_joke.start()
    
    logger.info("Entertainment module loaded")
