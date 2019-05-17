import {Injectable} from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';



@Injectable()
export class DatapoolsService {

    constructor(private service: Apollo) {}

    public getAllDatapools(node_id:string): QueryRef<any,any> {
        let controller_ip = JSON.parse(localStorage.getItem('controller'));
        return  this.service.watchQuery({
            query:  gql` query allDatapools($controller_ip: String,$node_id: String) {
                            datapools(controller_ip: $controller_ip,node_id: $node_id) {
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
            
                    `,
            variables: {
                method: 'GET',
                controller_ip: controller_ip,
                node_id: node_id
            }
        }) 
    }

}
