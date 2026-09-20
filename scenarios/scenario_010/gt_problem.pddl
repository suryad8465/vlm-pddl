(define (problem scenario_010)
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

    (connected kitchen living_room)
    (connected living_room kitchen)

    (located table kitchen)
    (located mug kitchen)
    (on mug table)
    (manipulable mug)
    (located kettle kitchen)
    (on kettle table)
    (manipulable kettle)
  )

  (:goal
    (robot-at kitchen)
  )
)
