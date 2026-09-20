(define (problem bring-mug-to-living-room)

  (:domain household)

  (:objects
    kitchen living-room - location
    robot table mug kettle - object
  )

  (:init

    ;; --------------------------------------------------------
    ;; Robot position
    ;; --------------------------------------------------------

    (robot-at living-room)


    ;; --------------------------------------------------------
    ;; Navigation
    ;; --------------------------------------------------------

    (connected living-room kitchen)
    (connected kitchen living-room)


    ;; --------------------------------------------------------
    ;; Objects and their locations
    ;; --------------------------------------------------------

    (located table kitchen)
    (located mug kitchen)
    (located kettle kitchen)


    ;; --------------------------------------------------------
    ;; Objects on the table
    ;; --------------------------------------------------------

    (on mug table)
    (on kettle table)


    ;; --------------------------------------------------------
    ;; Manipulable objects
    ;; --------------------------------------------------------

    (manipulable mug)
    (manipulable kettle)

  )

  (:goal
    (and
      (robot-at living-room)
      (on mug table)
    )
  )

)
