import PropTypes from "prop-types";
import React, { Component } from "react";
import {
  Button,
  Container,
  Divider,
  Form,
  Icon,
  Responsive,
  Segment,
  Sidebar,
  Visibility,
  Message,
  Progress,
  Loader,
  Image,
  Dimmer
} from "semantic-ui-react";
import axios from 'axios';
import {authAxios} from "../store/utility";
import {fileUploadURL, facialRecognitionURL} from "../constants";
import testface from "../assets/images/face.png";
import shortPara from "../assets/images/short_paragraph.png";


const getWidth = () => {
  const isSSR = typeof window === "undefined";
  return isSSR ? Responsive.onlyTablet.minWidth : window.innerWidth;
};

class DesktopContainer extends Component {
  state = {};

  hideFixedMenu = () => this.setState({ fixed: false });
  showFixedMenu = () => this.setState({ fixed: true });

  render() {
    const { children } = this.props;
    const { fixed } = this.state;

    return (
      <Responsive getWidth={getWidth} minWidth={Responsive.onlyTablet.minWidth}>
        <Visibility
          once={false}
          onBottomPassed={this.showFixedMenu}
          onBottomPassedReverse={this.hideFixedMenu}
        />
        {children}
      </Responsive>
    );
  }
}

DesktopContainer.propTypes = {
  children: PropTypes.node
};

class MobileContainer extends Component {
  state = {};

  handleSidebarHide = () => this.setState({ sidebarOpened: false });

  handleToggle = () => this.setState({ sidebarOpened: true });

  render() {
    const { children } = this.props;
    const { sidebarOpened } = this.state;

    return (
      <Responsive
        as={Sidebar.Pushable}
        getWidth={getWidth}
        maxWidth={Responsive.onlyMobile.maxWidth}
      >
        {children}
      </Responsive>
    );
  }
}

MobileContainer.propTypes = {
  children: PropTypes.node
};

const ResponsiveContainer = ({ children }) => (
  <div>
    <DesktopContainer>{children}</DesktopContainer>
    <MobileContainer>{children}</MobileContainer>
  </div>
);

ResponsiveContainer.propTypes = {
  children: PropTypes.node
};

class Demo extends React.Component {

    state = {
        fileName : "",
        file: null,
        error:null,
        loading: false,
        spinner :false,
        statusCode: null,
        progress : 0,
        data :null
    }

    handleFileChange = e => {
      if (e.target.files[0]){
        const size = e.target.files[0].size;
        if(size>5000000){
          this.setState({ error:"Image size is greater than 5MB" })
        }
        else{
          this.setState({
            fileName: e.target.files[0].name,
            file: e.target.files[0],
            error: null
        });
        }
      }  
      
    };

    handleSubmit = e =>{
        e.preventDefault();
        if(this.state.file){
            this.handleFileUpload(this.state.file);
        } else {
            this.setState({
                error: "No file Selected"
            });
        }
    };

    handleFileUpload = async file => {
        const __demo_class = this;
        const formData = new FormData();
        formData.append("file", file);
        this.setState({loading:true});
        const config = {
            onUploadProgress: function(progressEvent){
                const progress = Math.round( 100 *  progressEvent.loaded / progressEvent.total);
                __demo_class.setState({
                    progress
                });
                if(progress === 100){
                    __demo_class.setState({
                        loading:false,
                        spinner: true
                    })
                }
            } 
        };
        axios.post(fileUploadURL, formData, config )
        .then(res => {
            this.setState({
                data : res.data,
                statusCode : res.status,
                laoding : false,
                spinner:false
            })
        })
        .catch(err => {
            this.setState({
                error: err.message,
                loading: false,
                spinner:false
            });
        });
    };

    render(){

        const {error} = this.state;
        const {progress, loading,spinner,data} = this.state;
        return (
            <Container style={{padding: '1em',  marginBottom: "15em" }}>
              <Segment style={{ padding: "8em 0em"}} vertical>
                <Divider horizontal>Try uploading an image</Divider>
                <Form onSubmit={this.handleSubmit}>
                    <Form.Field>
                      <label>File Input & Upload</label>
                      <Button as="label" htmlFor="file" type="button" animated="fade">
                          <Button.Content visible>
                              <Icon name="file" />
                          </Button.Content>
                          <Button.Content hidden>
                              Choose a File( MAX 2MB)
                          </Button.Content>
                      </Button>
                      <input id='file' type='file' hidden onChange={this.handleFileChange}/>
                      <Form.Input fluid label="File Chosen:" placeholder="Use the above bar to browse your file system" readOnly value={this.state.fileName} />
                      <Button primary type="submit">
                        Upload
                      </Button>
                      <a classname="ui button" href={testface} download>
                          <i aria-hidden='true' className="download icon"></i>Download Test Image
                      </a>
                    </Form.Field>
                    
                </Form>
                {error && <Message error header="There was an error" content={error} />}
              </Segment>
              <Segment vertical>
                    <Divider horizontal>
                        Endpoint
                    </Divider>
                    <p>POST to {facialRecognitionURL} with headers: "Authentication": "Token {'<your_token>'} "</p>
              </Segment>
              <Segment vertical>
                    <Divider horizontal >
                        JSON Response
                    </Divider>
                    {loading && <Progress style={{marginTop: "20px"}} percent={progress} indicating progress > File Upload Progress </Progress>}
              </Segment>
                    {spinner &&  <Segment>
                        <Dimmer active inverted>
                            <Loader inverted>Detecting faces..</Loader>
                        </Dimmer>
                        <Image src={shortPara} />
                    </Segment> }
                    {
                        data && 
                        <div>
                            <pre>
                                {JSON.stringify(data, null, 2)}
                            </pre>
                        </div>

                    }
            </Container>
          );
    }
} 
export default Demo;
