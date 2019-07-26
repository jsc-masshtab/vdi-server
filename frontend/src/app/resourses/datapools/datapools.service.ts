import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class DatapoolsService {

    constructor(private service: Apollo) {}

    public getAllDatapools(node_id?:string): QueryRef<any,any> {
     
        if(node_id) {
            return  this.service.watchQuery({
                query:  gql` query allDatapools($node_id: String) {
                                controllers {
                                    datapools(node_id: $node_id) {
                                        id
                                        used_space
                                        free_space
                                        size
                                        status
                                        type
                                        vdisk_count
                                        file_count
                                        iso_count
                                        verbose_name
                                    }
                                }
                            }
                
                        `,
                variables: {
                    method: 'GET',
                    node_id: node_id
                }
            }) 
        } else {
            return  this.service.watchQuery({
                query:  gql` query allDatapools {
                                controllers {
                                    datapools {
                                        id
                                        used_space
                                        free_space
                                        size
                                        status
                                        type
                                        vdisk_count
                                        file_count
                                        iso_count
                                        verbose_name
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
