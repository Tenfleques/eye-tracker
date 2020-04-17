/*
COPYRIGHT 2018-2019  - PROPERTY OF TOBII AB
-------------------------------------
2018-2019 TOBII AB - KARLSROVAGEN 2D, DANDERYD 182 53, SWEDEN - All Rights Reserved.

NOTICE:  All information contained herein is, and remains, the property of Tobii AB and its suppliers, if any.
The intellectual and technical concepts contained herein are proprietary to Tobii AB and its suppliers and may be
covered by U.S.and Foreign Patents, patent applications, and are protected by trade secret or copyright law.
Dissemination of this information or reproduction of this material is strictly forbidden unless prior written
permission is obtained from Tobii AB.
*/

#pragma once
#include "../api/typedefs.h" // Fixed for C-Binding

typedef enum IL_Presence
{
    IL_Presence_Unknown,
    IL_Presence_Away,
    IL_Presence_Present,
} IL_Presence;

typedef struct IL_PresenceData
{
    IL_Timestamp timestamp_us;
    IL_Presence presence;
} IL_PresenceData;

#ifdef __cplusplus
namespace IL
{
    enum class Presence
    {
        Unknown = ::IL_Presence_Unknown,
        Away    = ::IL_Presence_Away,
        Present = ::IL_Presence_Present,
    };
    
    using PresenceData = ::IL_PresenceData;

    template <>
    const PresenceData& Empty<PresenceData>();
}

bool operator==(const IL::PresenceData& lhs, const IL::PresenceData& rhs);
#endif
