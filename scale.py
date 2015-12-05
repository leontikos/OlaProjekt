#rating scale
ratingScale = visual.RatingScale(win)
item = visual.TextStim(win, text = "Jesteś reptilianinem?")
while ratingScale.noResponse:
    item.draw()
    ratingScale.draw()
    win.flip()
rating = ratingScale.getRating()
decisionTime = ratingScale.getRT()
choiceHistory = ratingScale.getHistory()

#print rating, decisionTime, choiceHistory