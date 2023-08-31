# Topics in 10 K fillings 

This repo contains a series of utilities that
allow the extraction of topics from three sections of the annual filings for a range of approximately 500 companies and for a period of 4 years. 
The target user for this application can  follow the [User Guide](UserGuide) to get started with this web service.



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

### Organization of the repo
The repo is composed of two basic units: Four explanatory notebooks and an api with multiple endpoints. 
It also contains the dockerfiles and other files required for a deployment in docker.

### Raw Data Used
The raw data is a table with the following attributes:
    

### Pre-Processing 

### API REFERENCE

[![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)