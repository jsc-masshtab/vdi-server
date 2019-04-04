
import { Component } from '@angular/core';


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})

export class AppComponent  {


  constructor(){

  }

  ngOnInit() {

    
  }



  // private createTeplate() {
  //   this.service.mutate<any>({
  //     mutation: gql`  
  //                   mutation {
  //                     createTemplate(image_name: "image") {
  //                       template {
  //                         id
  //                       }
  //                     }
  //                   }
                  
      
  //   `,
  //   variables: {
  //     method: 'POST'
  //   }
  // }).subscribe(({ data, loading }) => {
  //     console.log(data,loading);
      
  //   });
  // }

}
