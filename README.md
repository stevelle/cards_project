# stevelle/cards_project
Model project for playing with frameworks and patterns

[![Build Status](https://travis-ci.org/stevelle/cards_project.svg?branch=master)](https://travis-ci.org/stevelle/cards_project)

This project is an experimental / model repository intended to test a selection of
frameworks and development and design patterns: 

### Frameworks and Libraries
 - The [Falcon](https://falconframework.org) REST API framework and several
related plugins are featured. 
 - Unit tests are built on [pytest](https://docs.pytest.org).


#### Development and Design Patterns
 - Some consideration is given to a Service Oriented Architecture (SOA), and some
   to the model of Microservices.
 - The project is organized as a [monorepo](https://danluu.com/monorepo/).
   Sub-projects contained in this repo are each [listed below](README.md/#sub-projects).
 - Some aspects of the Architecture will experimentally explore the use of 
   [Command Query Responsibility Separation (CQRS)](https://www.martinfowler.com/bliki/CQRS.html)
   to provide transactional integrity and view isolation to the complex
   changes expected in exercising the data models.

#### Unresolved concerns
 - API versioning
 - API discoverability
 - API Authc/Authz
 - API Caching

## Deploying
This project is just getting started. There is no deployment support, no model
chosen, and no appropriate tooling is provided at this time. 

For now the following command will start the card_table service

  `$ gunicorn -b 0.0.0.0:8000 card_table.server`

when working in an environment where the python 3 requirements have been met.

## Contributing
I thank you for your interest, but contributions are not invited at this time.

--- 
## Sub-projects

### card_table
Sub-project to manage the state of cards at a game table

