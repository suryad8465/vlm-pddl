(define (problem household-problem-1)
  (:domain household)

  (:objects
    kitchen living_room bedroom - location
    table mug kettle robot - object
  )

  (:init
    (robot-at living_room)
    (connected kitchen living_room)
    (connected living_room kitchen)
    (connected living_room bedroom)
    (connected bedroom living_room)
    (located table kitchen)
    (located mug kitchen)
    (located kettle kitchen)
    (on mug table)
    (on kettle table)
    (manipulable mug)
    (manipulable kettle)
  )

  (:goal
    (located mug bedroom)
  )
)