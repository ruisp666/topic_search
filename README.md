# Topics in 10 K fillings 

This repo contains a series of utilities that
allow the extraction of topics from three sections of the annual filings for a range of approximately 500 companies and for a period of 4 years. 
The target user for this application can  follow the [User Guide]("api/User Guide.ipynb") to get started with this web service.


The sections are the following, as per the [SEC guideline](reada10k.pdf)

> *Item 1
“Business” requires a description of the company’s business, including its main products and services,
> what subsidiaries it owns, and what markets it operates in. This section may also include information about recent events,
> competition the company faces, regulations that apply to it, labor issues, special operating costs,
or seasonal factors. This is a good place to start to understand how the company operates.*

> *Item1A
“Risk Factors” includes information about the most significant risks that apply to the company or to its securiies. 
> Companies generally list the risk factors in order of their importance.
In practice, this section focuses on the risks themselves, not how the company addresses those risks. 
> Some risks may be true for the entire economy, some may apply only to the company’s industry
> sector or geographic region, and some may be unique to the company.*

> *Item7
"Management’s Discussion and Analysis of Financial Condition and Results of Operations” gives the company’s
> perspective on the business results of the past financial year.
> This section, known as the MD&A for short, allows company management to tell its story in its own words.*
> 

### Notebooks

### Organization of the repo
The repo is composed of two basic units: Four explanatory notebooks and an api with multiple endpoints with a [tutorial]("api/User Guide.ipynb").
It also contains the dockerfiles and other files required for a deployment in docker, including a blank database.

### Raw Data Used
The raw data is a table with timestamps, date of filling, the raw text corresponding to a particular filed 10-k for Items1, ItemsA and Item7 of the 10-k.
It covers approximately 500 companies over a period of 4 years.

### Pre-Processing and Topic Modelling
For the top modelling we used [bertopic](https://maartengr.github.io/BERTopic/index.html#quick-start) with the default sentence transformer. We then used langchain token splitter to split the long texts into documents.
For splitting we used the same sentence transformer as for the embeddings. We also took into consideration stop words when building the topics. While the stop words do not enter the topics,
they are not excluded when tokenizing or encoding to preserve meaning.

### Testing

A suite of [tests](test_routes.py) was designed to ensure the functionality and consistency of the endpoints. As of this version, they all pass for the local version. 

### Further Development
In the next versions of this web service we will add more tests


[![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)