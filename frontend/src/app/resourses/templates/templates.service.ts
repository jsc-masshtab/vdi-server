import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class TemplatesService {

    constructor(private service: Apollo) {}

    public getAllTemplates(ip?:string): QueryRef<any,any> {

        if(ip) {
            return  this.service.watchQuery({
                query:  gql` query allTemplates($ip: String) {
                                    controller(ip: $ip) {
                                        templates {
                                            id
                                            info
                                        }  
                                    }
                                }
                         `,
                variables: {
                    method: 'GET',
                    ip: ip
                }
            })
        } else {
            return  this.service.watchQuery({
                query:  gql` query allTemplates {
                                    controllers {
                                        templates {
                                            id
                                            info
                                        }  
                                    }
                                }
                         `,
                variables: {
                    method: 'GET'
                }
            })
        }
    }

}
