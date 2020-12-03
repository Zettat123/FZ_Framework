import React from 'react'
import axios from 'axios'
import cx from 'classnames'
import styles from './App.scss'

const waitingMessage = 'Loading data, please wait...'
const yes = 'Yes'
const no = 'No'
const safeText = 'SAFE'
const dangerText = 'FIRE ALARM!'
const serverPort = 29600
const defaultHost = '192.168.1.101'

const hostname = location.hostname
let devUrl = `http://${
  hostname === 'localhost' ? defaultHost : hostname
}:${serverPort}/data`

class App extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      alarm: null,
      temprature: null,
      smoke: null,
      light: null,
      picture: null,
      prevRequestCompleted: true,
    }
  }

  componentDidMount() {
    let id = setInterval(() => {
      const { prevRequestCompleted } = this.state
      console.log(prevRequestCompleted)
      if (prevRequestCompleted) {
        this.setState({ prevRequestCompleted: false })
        axios
          .get(devUrl)
          .then(({ data }) => {
            console.log(data)
            const { alarm, hostname, temprature, smoke, light, picture } = data
            this.setState({
              alarm,
              hostname,
              smoke,
              light,
              picture,
              temprature,
            })
          })
          .finally(this.setState({ prevRequestCompleted: true }))
      }
    }, 1000 * 3)

    //clearInterval(id)
  }

  render() {
    const { alarm, hostname, temprature, smoke, light, picture } = this.state

    return (
      <div className={styles.root}>
        <div className={styles.title}>Fire Monitor</div>
        <div
          className={cx(styles.alarmBlock, alarm ? styles.danger : styles.safe)}
        >
          <div>{alarm ? dangerText : safeText}</div>
        </div>
        <div className={styles.item}>
          <div className={styles.itemName}>Current host</div>
          <div className={styles.itemValue}>
            {hostname == null ? waitingMessage : hostname}
          </div>
        </div>
        <div className={styles.item}>
          <div className={styles.itemName}>Temprature</div>
          <div className={styles.itemValue}>
            {temprature == null ? waitingMessage : temprature}
          </div>
        </div>

        <div className={styles.item}>
          <div className={styles.itemName}>Smoke</div>
          <div className={styles.itemValue}>
            {smoke == null ? waitingMessage : smoke === 1 ? yes : no}
          </div>
        </div>
        <div className={styles.item}>
          <div className={styles.itemName}>Light</div>
          <div className={styles.itemValue}>
            {light == null ? waitingMessage : light === 1 ? yes : no}
          </div>
        </div>
        {alarm === true && (
          <div className={styles.item}>
            <div className={styles.itemName}>Picture</div>
            <div className={styles.itemValue}>
              <img
                className={styles.imageItem}
                src={`data:image/png;base64,${picture}`}
              />
            </div>
          </div>
        )}
      </div>
    )
  }
}

export default App
