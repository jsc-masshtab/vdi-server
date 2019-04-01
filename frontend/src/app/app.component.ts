import { Component } from '@angular/core';
import { Apollo } from 'apollo-angular';
import gql from 'graphql-tag';
import { library } from '@fortawesome/fontawesome-svg-core';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent  {
  title = 'frontend';

  constructor(private service: Apollo){

  }

  ngOnInit() {
    this.getTeplates();
    //this.createTeplate();
console.log(library);
    

  }

  private getTeplates() {
    this.service.watchQuery<any>({
      query: gql` query allTemplates {
                    templates {
                      id
                      info
                    }
                  }
      
    `,
    variables: {
      method: 'GET'
    }
    })
      .valueChanges
      .subscribe(({ data, loading }) => {
       console.log(data,loading);
       
      });
  }

  private createTeplate() {
    this.service.mutate<any>({
      mutation: gql`  
                    mutation {
                      createTemplate(image_name: "image") {
                        template {
                          id
                        }
                      }
                    }
                  
      
    `,
    variables: {
      method: 'POST'
    }
  }).subscribe(({ data, loading }) => {
      console.log(data,loading);
      
    });
  }

}
