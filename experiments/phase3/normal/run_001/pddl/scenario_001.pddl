(define (problem go_to_kitchen)
  (:domain household)

  (:objects
    kitchen - location
    living_room - location
    table - object
    mug - object
    kettle - object
  )

  (:init
    (robot-at living_room)
    (connected living_room kitchen)
    (connected kitchen living_room)
    (located table kitchen)
    (located mug kitchen)
    (located kettle kitchen)
    (on mug table)
    (on kettle table)
    (manipulable mug)
    (manipulable kettle)
  )

  (:goal
    (robot-at kitchen)
  )
)