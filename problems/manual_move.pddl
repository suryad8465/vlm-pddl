(define (problem manual-move)
  (:domain household)

  (:objects
    kitchen living_room - location
  )

  (:init
    (robot-at living_room)
    (connected living_room kitchen)
    (connected kitchen living_room)
  )

  (:goal
    (robot-at kitchen)
  )
)
