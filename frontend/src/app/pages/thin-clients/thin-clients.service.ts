import { Injectable } from '@angular/core';
import { Apollo, QueryRef } from 'apollo-angular';
import gql from 'graphql-tag';

import { IParams } from '@shared/types';

@Injectable({
  providedIn: 'root'
})
export class ThinClientsService {

  public params: IParams = { // для несбрасывания параметров сортировки при всех обновлениях
    spin: true,
    nameSort: undefined
  };

  constructor(private service: Apollo) { }

  public getThinClients(queryset: any = {}): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query thin_clients(
          $ordering: ShortString
          $get_disconnected: Boolean
        ){
          thin_clients_count
          thin_clients(
            ordering: $ordering
            get_disconnected: $get_disconnected
          ){
            conn_id
            user_name
            user_id
            veil_connect_version
            vm_name
            tk_ip
            tk_os
            connected
            disconnected
            data_received
            last_interaction
            is_afk
            mac_address
            hostname
            connection_type
            is_connection_secure
            read_speed
            write_speed
            avg_rtt
            loss_percentage
          }
        }
      `,
      variables: {
        method: 'GET',
        ordering: this.params.nameSort,
        ...queryset
      }
    });
  }

  public getThinClient(queryset: any = {}): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query thin_clients($conn_id: UUID) {
          thin_client(conn_id: $conn_id){
            conn_id
            user_name
            veil_connect_version
            vm_name
            tk_ip
            tk_os
            connected
            disconnected
            data_received
            last_interaction
            is_afk
            connection_type
            is_connection_secure
            read_speed
            write_speed
            avg_rtt
            loss_percentage
            mac_address
            hostname
          }
        }
      `,
      variables: {
        method: 'GET',
        ...queryset
      }
    });
  }

  public getThinClientStatistic(queryset: any = {}): QueryRef<any, any> {
    return this.service.watchQuery({
      query: gql`
        query thin_clients(
          $limit: Int
          $offset: Int
          $ordering: ShortString
          $conn_id: UUID
          $user_id: UUID
        ){
          thin_clients_statistics(
            limit: $limit
            offset: $offset
            ordering: $ordering
            conn_id: $conn_id
            user_id: $user_id
          ){
            id
            conn_id
            message
            created
          }
        }
    `,
      variables: {
        method: 'GET',
        ordering: this.params.nameSort,
        ...queryset
      }
    });
  }

  sendMessageToThinClient(recipient_id, message) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation thin_clients($recipient_id: UUID, $message: ShortString!) {
          sendMessageToThinClient(
            recipient_id: $recipient_id,
            message: $message,
          ){
            ok
          }
        }`,
      variables: {
        method: 'POST',
        recipient_id,
        message
      }
    })
  }

  disconnectThinClient(conn_id: string) {
    return this.service.mutate<any>({
      mutation: gql`
        mutation thin_clients($conn_id: UUID!) {
          disconnectThinClient(conn_id: $conn_id) {
            ok
          }
        }
      `,
      variables: {
        method: 'POST',
        conn_id
      }
    });
  }

}
