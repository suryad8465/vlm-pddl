(define (problem manual-test)
  (:domain household)

  (:objects
    kitchen living_room - location
    table mug - object
  )

  (:init
    (robot-at kitchen)

    (connected kitchen living_room)
    (connected living_room kitchen)

    (located mug kitchen)
    (on mug table)

    (manipulable mug)
  )

  (:goal
    (holding mug)
  )
)
