import io
import base64
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter

def generate_word_cloud_base64(text):
    wordcloud = WordCloud(width=600, height=300, background_color='white').generate(text)
    img_io = io.BytesIO()
    wordcloud.to_image().save(img_io, format='PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode()

def generate_similarity_pie_chart_base64(similarity_score):
    labels = ['Similarity', 'Uniqueness']
    sizes = [similarity_score, 100 - similarity_score]
    colors = ['#FF6B6B', '#6BCB77']

    plt.figure(figsize=(5, 5))
    plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=140,
        wedgeprops={'edgecolor': 'white'}
    )
    plt.axis('equal')
    plt.title('Document Similarity Breakdown')

    img_io = io.BytesIO()
    plt.savefig(img_io, format='PNG', bbox_inches='tight')
    plt.close()
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode()

def generate_word_frequency_chart(text1, text2):
    words1 = Counter(text1.lower().split())
    words2 = Counter(text2.lower().split())

    common_words = set(words1.keys()) & set(words2.keys())

    if not common_words:
        return None 

    word_counts = {word: words1[word] + words2[word] for word in common_words}

    top_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    labels, values = zip(*top_words) if top_words else ([], [])

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=['#FF6B6B', '#6BCB77', '#4D96FF', '#FFA500', '#A569BD'])
    plt.title('Top Common Words in Both Documents')
    plt.ylabel('Frequency')

    img_io = io.BytesIO()
    plt.savefig(img_io, format='PNG', bbox_inches='tight')
    plt.close()
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode()

# Call all visualizations in one function
def generate_visualizations(text1, text2, similarity_score):
    wordcloud1 = generate_word_cloud_base64(text1)
    similarity_chart = generate_similarity_pie_chart_base64(similarity_score)
    word_freq_chart = generate_word_frequency_chart(text1, text2)

    return wordcloud1, similarity_chart, word_freq_chart
