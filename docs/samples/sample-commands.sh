# Demo software project items
giantt log demo0 "Creating demonstration Giantt items with interdependencies for project showcase" --tags demo,showcase,example
giantt add app_prototype "Create initial app prototype" --duration 2w --charts "Demo Project" --tags demo,software,prototype --status NOT_STARTED --priority HIGH
giantt add market_research "Conduct market research for target audience" --duration 1w --charts "Demo Project" --tags demo,research,planning --status NOT_STARTED --priority MEDIUM
giantt add ui_design "Design user interface mockups" --duration 5d --charts "Demo Project" --tags demo,design,ui --status NOT_STARTED --priority HIGH --requires market_research
giantt add backend_api "Develop backend API endpoints" --duration 10d --charts "Demo Project" --tags demo,software,backend --status NOT_STARTED --priority MEDIUM --requires market_research
giantt add frontend_dev "Implement frontend components" --duration 8d --charts "Demo Project" --tags demo,software,frontend --status NOT_STARTED --priority HIGH --requires ui_design
giantt add integration_test "Integrate and test frontend with backend" --duration 3d --charts "Demo Project" --tags demo,testing,integration --status NOT_STARTED --priority MEDIUM --requires "frontend_dev,backend_api"
giantt add user_testing "Conduct user testing sessions" --duration 4d --charts "Demo Project" --tags demo,testing,users --status NOT_STARTED --priority HIGH --requires app_prototype
giantt add bug_fixes "Address issues from user testing" --duration 5d --charts "Demo Project" --tags demo,software,bugfix --status NOT_STARTED --priority MEDIUM --requires user_testing
giantt add demo_preparation "Prepare demonstration materials" --duration 2d --charts "Demo Project" --tags demo,presentation --status NOT_STARTED --priority MEDIUM --requires integration_test
giantt add stakeholder_demo "Present to key stakeholders" --duration 1d --charts "Demo Project" --tags demo,presentation,milestone --status NOT_STARTED --priority HIGH --requires "demo_preparation,bug_fixes"
giantt modify app_prototype requires "integration_test"
giantt set-status market_research IN_PROGRESS
giantt log demo0 "Completed creation of interconnected demo items showing a small software project lifecycle with dependencies" --tags demo,complete
# Demo watermelon farming project
giantt log melon0 "Creating demonstration items for watermelon farming seasonal planning" --tags demo,agriculture,watermelon,melon0
giantt add soil_testing "Test soil pH and nutrient levels" --duration 3d --charts "Watermelon Farm" --tags melon0,preparation,soil --status NOT_STARTED --priority MEDIUM
giantt add field_preparation "Prepare and till field for planting" --duration 1w --charts "Watermelon Farm" --tags melon0,preparation,equipment --status NOT_STARTED --priority HIGH --requires soil_testing
giantt add seed_selection "Select watermelon varieties suited to local climate" --duration 2d --charts "Watermelon Farm" --tags melon0,planning,seeds --status NOT_STARTED --priority HIGH
giantt add irrigation_setup "Install drip irrigation system" --duration 5d --charts "Watermelon Farm" --tags melon0,infrastructure,water --status NOT_STARTED --priority CRITICAL --requires field_preparation
giantt add seedling_start "Start seedlings in greenhouse" --duration 3w --charts "Watermelon Farm" --tags melon0,growth,greenhouse --status NOT_STARTED --priority MEDIUM --requires seed_selection
giantt add transplanting "Transplant seedlings to field" --duration 4d --charts "Watermelon Farm" --tags melon0,growth,planting --status NOT_STARTED --priority HIGH --requires "seedling_start,irrigation_setup"
giantt add pest_management "Implement pest management strategy" --duration 2d --charts "Watermelon Farm" --tags melon0,maintenance,pests --status NOT_STARTED --priority MEDIUM --requires transplanting
giantt add weed_control "Regular weeding and maintenance" --duration "2mo3w" --charts "Watermelon Farm" --tags melon0,maintenance,weeds --status NOT_STARTED --priority MEDIUM --requires transplanting
giantt add pollination_check "Monitor and support pollinator activity" --duration 3w --charts "Watermelon Farm" --tags melon0,growth,pollinators --status NOT_STARTED --priority MEDIUM --requires transplanting
giantt add harvest_planning "Plan harvest logistics and labor" --duration 1w --charts "Watermelon Farm" --tags melon0,planning,harvest --status NOT_STARTED --priority HIGH --requires "transplanting"
giantt add fruit_harvesting "Harvest ripe watermelons" --duration "2w3d" --charts "Watermelon Farm" --tags melon0,harvest,labor --status NOT_STARTED --priority CRITICAL --requires "weed_control,pollination_check"
giantt add market_delivery "Transport and deliver to markets" --duration 3d --charts "Watermelon Farm" --tags melon0,market,distribution --status NOT_STARTED --priority HIGH --requires fruit_harvesting
giantt add season_review "Analyze season successes and failures" --duration 2d --charts "Watermelon Farm" --tags melon0,analysis,planning --status NOT_STARTED --priority MEDIUM --requires market_delivery
giantt set-status soil_testing COMPLETED
giantt set-status seed_selection IN_PROGRESS
giantt log melon0 "Completed watermelon farming example showing seasonal planning cycle with dependencies between preparation, planting, maintenance, and harvest phases" --tags demo,complete,melon0